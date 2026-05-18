import time
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

API_BASE = "http://localhost:8081"
BOT_API_KEY = "lY54m5h3kA2W4nLo8eoeOWr6IvNhnGkBO6mdcSakGVI"
HEADERS = {"Content-Type": "application/json", "X-Bot-Key": BOT_API_KEY}

CHECKPOINT_FILE = Path("scraper_checkpoint.json")


def load_checkpoint() -> int:
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text())
        pagina = data.get("pagina_concluida", 0)
        print(f"[CHECKPOINT] Retomando da pagina {pagina + 1}")
        return pagina
    return 0


def save_checkpoint(pagina: int):
    CHECKPOINT_FILE.write_text(json.dumps({"pagina_concluida": pagina}))



def salvar_projeto(proj: dict) -> int | None:
    payload = {
        "numero":            proj["numero"],
        "titulo":            proj["titulo"],
        "dataInicio":        _parse_date_iso(proj["inicio"]),
        "dataFim":           _parse_date_iso(proj["fim"]),
        "situacao":          proj["situacao"],
        "resumo":            proj["resumo"],
        "responsavel":       proj["coordenador"],
        "classificacaoCNPQ": proj["classificacao_cnpq"],
        "linhaPesquisa":     proj["linha_pesquisa"],
        "tipoOrientacao":    proj["tipo_orientacao"],
    }
    resp = requests.post(f"{API_BASE}/projetos", json=payload, headers=HEADERS)
    if resp.status_code == 200:
        projeto_id = resp.json()["id"]
        print(f"  [OK] {proj['numero']} (id={projeto_id})")
        return projeto_id
    elif resp.status_code == 409:
        print(f"  [SKIP] {proj['numero']} ja existe")
        return None
    else:
        print(f"  [ERRO] {proj['numero']}: {resp.status_code} - {resp.text}")
        return None


def upsert_topico(nome: str) -> int | None:
    if not nome:
        return None
    resp = requests.post(f"{API_BASE}/topicos", json={"nome": nome}, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()["id"]
    print(f"  [ERRO] Topico '{nome}': {resp.status_code}")
    return None


def vincular_projeto_topico(projeto_id: int, topico_id: int):
    resp = requests.post(
        f"{API_BASE}/projeto-topicos",
        json={"projetoId": projeto_id, "topicoId": topico_id},
        headers=HEADERS,
    )
    if resp.status_code not in (200, 409):
        print(f"  [ERRO] Vinculo {projeto_id}x{topico_id}: {resp.status_code}")


def salvar_palavras_chave(projeto_id: int, proj: dict):
    for i in range(1, 5):
        palavra = proj.get(f"palavra_{i}")
        if not palavra:
            continue
        topico_id = upsert_topico(palavra)
        if topico_id:
            vincular_projeto_topico(projeto_id, topico_id)


def salvar_tudo(proj: dict):
    """Salva projeto + palavras-chave. Chamado em thread paralela."""
    projeto_id = salvar_projeto(proj)
    if projeto_id:
        salvar_palavras_chave(projeto_id, proj)


def _parse_date_iso(valor: str) -> str | None:
    try:
        from datetime import datetime
        return datetime.strptime(valor, "%d/%m/%Y").date().isoformat()
    except Exception:
        return None

driver = webdriver.Chrome()
BASE_URL = "https://portal.ufsm.br/projetos/publico/projetos/list.html"
driver.get(BASE_URL)
wait = WebDriverWait(driver, 10)


def clicar_pesquisar():
    try:
        botao = wait.until(EC.element_to_be_clickable((By.ID, "search-btn")))
        driver.execute_script("arguments[0].click();", botao)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    except Exception as e:
        print("Erro ao pesquisar:", e)


def set_items_per_page_100():
    try:
        select_el = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "select.selectfield.width-auto")
        ))
        sel = Select(select_el)
        if sel.first_selected_option.get_attribute("value") == "100":
            return
        # usa indice: ultima opcao = maior quantidade
        sel.select_by_index(len(sel.options) - 1)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        time.sleep(0.5)
    except Exception as e:
        print("Aviso: nao foi possivel mudar para 100 por pagina:", e)


def ir_para_pagina(numero: int):
    if numero <= 1:
        return
    try:
        input_el = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.textfield[placeholder='Ir para...']")
        ))
        input_el.clear()
        input_el.send_keys(str(numero))
        input_el.send_keys(Keys.ENTER)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        time.sleep(0.8)
    except Exception as e:
        print(f"  Aviso: nao foi possivel ir para pagina {numero}:", e)


def voltar_para_pagina(pagina: int):
    """Volta pra listagem e vai direto pra pagina certa (1 navegacao + 1 input)."""
    driver.get(BASE_URL)
    clicar_pesquisar()
    set_items_per_page_100()
    ir_para_pagina(pagina)


def buscar_campo_por_label(label):
    try:
        el = driver.find_element(
            By.XPATH, f"//span[text()='{label}']/following-sibling::span"
        )
        return el.text.strip()
    except Exception:
        return ""


def buscar_classificacoes() -> dict:
    result = {"classificacao_cnpq": "", "linha_pesquisa": "", "tipo_orientacao": ""}
    try:
        linhas = driver.find_elements(By.CSS_SELECTOR, ".panel-content .table .tbody .tr")
        for linha in linhas:
            cols = linha.find_elements(By.CSS_SELECTOR, ".td")
            if len(cols) < 2:
                continue
            tipo, valor = cols[0].text.strip(), cols[1].text.strip()
            if tipo == "Classificacao CNPq":
                result["classificacao_cnpq"] = valor
            elif tipo == "Linha de pesquisa":
                result["linha_pesquisa"] = valor
            elif tipo == "Quanto ao tipo de orientacao":
                result["tipo_orientacao"] = valor
    except Exception:
        pass
    return result


def extrair_detalhes(proj: dict) -> dict:
    """Abre a URL do projeto e extrai todos os campos extras."""
    driver.get(proj["url"])
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    proj["resumo"]    = buscar_campo_por_label("Resumo")
    proj["palavra_1"] = buscar_campo_por_label("Palavra-chave 1")
    proj["palavra_2"] = buscar_campo_por_label("Palavra-chave 2")
    proj["palavra_3"] = buscar_campo_por_label("Palavra-chave 3")
    proj["palavra_4"] = buscar_campo_por_label("Palavra-chave 4")
    proj.update(buscar_classificacoes())

    coordenador = ""
    try:
        participantes = driver.find_elements(
            By.CSS_SELECTOR, "#paginationWrapperParticipantes tbody tr"
        )
        for p in participantes:
            tds = p.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 4 and "Coordenador" in tds[3].text:
                coordenador = tds[2].text.strip()
                break
    except Exception:
        pass
    proj["coordenador"] = coordenador
    return proj


pagina_inicial = load_checkpoint() + 1
pagina = pagina_inicial

clicar_pesquisar()
set_items_per_page_100()

if pagina > 1:
    ir_para_pagina(pagina)

try:
    while True:
        print(f"\n=== Pagina {pagina} ===")

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except Exception:
            break

        linhas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if not linhas:
            break

        projetos_basicos = []
        for linha in linhas:
            cols = linha.find_elements(By.TAG_NAME, "td")
            if len(cols) < 6:
                continue
            try:
                link = linha.find_element(By.CSS_SELECTOR, "a[title='Abrir']")
                projetos_basicos.append({
                    "numero":   cols[1].text,
                    "titulo":   cols[2].text,
                    "inicio":   cols[3].text,
                    "fim":      cols[4].text,
                    "situacao": cols[5].text,
                    "url":      link.get_attribute("href"),
                })
            except Exception:
                continue

        print(f"  {len(projetos_basicos)} projetos coletados da listagem")

        projetos_completos = []
        for proj in projetos_basicos:
            try:
                proj = extrair_detalhes(proj)
                print(f"  Extraido: {proj['numero']} - {proj['titulo'][:50]}")
                projetos_completos.append(proj)
            except Exception as e:
                print(f"  Erro ao extrair {proj.get('numero', '?')}: {e}")

        print(f"  Salvando {len(projetos_completos)} projetos na API...")
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(salvar_tudo, p): p["numero"] for p in projetos_completos}
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as e:
                    print(f"  Erro ao salvar {futures[fut]}: {e}")

    
        save_checkpoint(pagina)

        try:
            voltar_para_pagina(pagina)
            next_li = wait.until(EC.presence_of_element_located((By.ID, "next_1")))
            if "disabled" in next_li.get_attribute("class"):
                print("Ultima pagina atingida.")
                break
            next_btn = next_li.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", next_btn)
            pagina += 1
            time.sleep(1.5)
        except Exception as e:
            print("Erro ao avancar pagina:", e)
            break

finally:
    driver.quit()
    print("\nScraping concluido.")