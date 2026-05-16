import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



API_BASE = "http://localhost:8081"
BOT_API_KEY = "lY54m5h3kA2W4nLo8eoeOWr6IvNhnGkBO6mdcSakGVI"  # mesmo valor que vai no filtro do Spring

HEADERS = {
    "Content-Type": "application/json",
    "X-Bot-Key": BOT_API_KEY,
}


def salvar_projeto(proj: dict) -> int | None:
    payload = {
        "numero":           proj["numero"],
        "titulo":           proj["titulo"],
        "dataInicio":       _parse_date_iso(proj["inicio"]),
        "dataFim":          _parse_date_iso(proj["fim"]),
        "situacao":         proj["situacao"],
        "resumo":           proj["resumo"],
        "responsavel":      proj["coordenador"],
        "classificacaoCNPQ": proj["classificacao_cnpq"],
        "linhaPesquisa":    proj["linha_pesquisa"],
        "tipoOrientacao":   proj["tipo_orientacao"],
    }

    resp = requests.post(f"{API_BASE}/projetos", json=payload, headers=HEADERS)

    if resp.status_code == 200:
        projeto_id = resp.json()["id"]
        print(f"  [OK] Projeto {proj['numero']} salvo (id={projeto_id})")
        return projeto_id
    elif resp.status_code == 409:
        print(f"  [SKIP] Projeto {proj['numero']} já existe")
        return None
    else:
        print(f"  [ERRO] Projeto {proj['numero']}: {resp.status_code} - {resp.text}")
        return None


def upsert_topico(nome: str) -> int | None:
    if not nome:
        return None

    resp = requests.post(f"{API_BASE}/topicos", json={"nome": nome}, headers=HEADERS)

    if resp.status_code == 200:
        return resp.json()["id"]
    else:
        print(f"  [ERRO] Tópico '{nome}': {resp.status_code} - {resp.text}")
        return None


def vincular_projeto_topico(projeto_id: int, topico_id: int) -> None:
    resp = requests.post(
        f"{API_BASE}/projeto-topicos",
        json={"projetoId": projeto_id, "topicoId": topico_id},
        headers=HEADERS,
    )

    if resp.status_code == 200:
        pass  # vinculado com sucesso
    elif resp.status_code == 409:
        pass  # já existia, tudo bem
    else:
        print(f"  [ERRO] Vínculo {projeto_id}x{topico_id}: {resp.status_code} - {resp.text}")


def salvar_palavras_chave(projeto_id: int, proj: dict) -> None:
    palavras = [
        proj.get("palavra_1"),
        proj.get("palavra_2"),
        proj.get("palavra_3"),
        proj.get("palavra_4"),
    ]
    for palavra in palavras:
        if not palavra:
            continue
        topico_id = upsert_topico(palavra)
        if topico_id:
            vincular_projeto_topico(projeto_id, topico_id)


def _parse_date_iso(valor: str) -> str | None:
    """Converte dd/mm/yyyy para yyyy-mm-dd (formato que o Spring espera)."""
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


def ir_para_pagina(numero):
    for _ in range(numero - 1):
        try:
            next_li = wait.until(EC.presence_of_element_located((By.ID, "next_1")))
            if "disabled" in next_li.get_attribute("class"):
                return
            next_button = next_li.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
        except Exception:
            return


def buscar_campo_por_label(label):
    try:
        elemento = driver.find_element(
            By.XPATH,
            f"//span[text()='{label}']/following-sibling::span",
        )
        return elemento.text.strip()
    except Exception:
        return ""


def buscar_classificacoes():
    classificacao_cnpq = ""
    linha_pesquisa = ""
    tipo_orientacao = ""
    try:
        linhas = driver.find_elements(By.CSS_SELECTOR, ".panel-content .table .tbody .tr")
        for linha in linhas:
            colunas = linha.find_elements(By.CSS_SELECTOR, ".td")
            if len(colunas) < 2:
                continue
            tipo = colunas[0].text.strip()
            valor = colunas[1].text.strip()
            if tipo == "Classificação CNPq":
                classificacao_cnpq = valor
            elif tipo == "Linha de pesquisa":
                linha_pesquisa = valor
            elif tipo == "Quanto ao tipo de orientação":
                tipo_orientacao = valor
    except Exception:
        pass
    return {
        "classificacao_cnpq": classificacao_cnpq,
        "linha_pesquisa":     linha_pesquisa,
        "tipo_orientacao":    tipo_orientacao,
    }



pagina = 1
clicar_pesquisar()

try:
    while True:
        print(f"\n=== Página {pagina} ===")

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except Exception:
            break

        linhas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if not linhas:
            break

        projetos = []
        for linha in linhas:
            colunas = linha.find_elements(By.TAG_NAME, "td")
            if len(colunas) < 6:
                continue
            try:
                link = linha.find_element(By.CSS_SELECTOR, "a[title='Abrir']")
                url = link.get_attribute("href")
                projetos.append({
                    "numero":   colunas[1].text,
                    "titulo":   colunas[2].text,
                    "inicio":   colunas[3].text,
                    "fim":      colunas[4].text,
                    "situacao": colunas[5].text,
                    "url":      url,
                })
            except Exception:
                continue

        for proj in projetos:
            try:
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
                    for participante in participantes:
                        tds = participante.find_elements(By.TAG_NAME, "td")
                        if len(tds) >= 4 and "Coordenador" in tds[3].text:
                            coordenador = tds[2].text.strip()
                            break
                except Exception:
                    pass

                proj["coordenador"] = coordenador

                print(f"\nProcessando: {proj['numero']} - {proj['titulo'][:60]}")

                projeto_id = salvar_projeto(proj)
                if projeto_id:
                    salvar_palavras_chave(projeto_id, proj)

            except Exception as e:
                print("Erro projeto:", e)
            finally:
                driver.get(BASE_URL)
                clicar_pesquisar()
                ir_para_pagina(pagina)

        # próxima página
        try:
            next_li = wait.until(EC.presence_of_element_located((By.ID, "next_1")))
            if "disabled" in next_li.get_attribute("class"):
                break
            next_button = next_li.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", next_button)
            pagina += 1
            time.sleep(3)
        except Exception:
            break

finally:
    driver.quit()