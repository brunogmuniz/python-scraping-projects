import time
import psycopg
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DB_DSN = "postgresql://postgres:postgres@localhost:5433/ufsm"

def get_conn():
    return psycopg.connect(DB_DSN)


def salvar_projeto(conn, proj: dict) -> int | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM projetos WHERE numero = %s", (proj["numero"],))
        row = cur.fetchone()
        if row:
            print(f"  [SKIP] Projeto {proj['numero']} já existe (id={row[0]})")
            return row[0]

        cur.execute(
            """
            INSERT INTO projetos
                (numero, titulo, data_inicio, data_fim, situacao, resumo,
                 url, responsavel, classificacao_cnpq, linha_pesquisa, tipo_orientacao)
            VALUES
                (%(numero)s, %(titulo)s, %(data_inicio)s, %(data_fim)s, %(situacao)s,
                 %(resumo)s, %(url)s, %(responsavel)s, %(classificacao_cnpq)s,
                 %(linha_pesquisa)s, %(tipo_orientacao)s)
            RETURNING id
            """,
            {
                "numero":             proj["numero"],
                "titulo":             proj["titulo"],
                "data_inicio":        _parse_date(proj["inicio"]),
                "data_fim":           _parse_date(proj["fim"]),
                "situacao":           proj["situacao"],
                "resumo":             proj["resumo"],
                "url":                proj.get("url", ""),
                "responsavel":        proj["coordenador"],
                "classificacao_cnpq": proj["classificacao_cnpq"],
                "linha_pesquisa":     proj["linha_pesquisa"],
                "tipo_orientacao":    proj["tipo_orientacao"],
            },
        )
        projeto_id = cur.fetchone()[0]
        conn.commit()
        print(f"  [OK] Projeto {proj['numero']} inserido (id={projeto_id})")
        return projeto_id


def upsert_topico(conn, nome: str) -> int | None:
    if not nome:
        return None

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM topicos WHERE nome = %s", (nome,))
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute("INSERT INTO topicos (nome) VALUES (%s) RETURNING id", (nome,))
        topico_id = cur.fetchone()[0]
        conn.commit()
        return topico_id


def vincular_projeto_topico(conn, projeto_id: int, topico_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM projeto_topicos WHERE projeto_id = %s AND topico_id = %s",
            (projeto_id, topico_id),
        )
        if cur.fetchone():
            return

        cur.execute(
            "INSERT INTO projeto_topicos (projeto_id, topico_id) VALUES (%s, %s)",
            (projeto_id, topico_id),
        )
        conn.commit()


def salvar_palavras_chave(conn, projeto_id: int, proj: dict) -> None:
    palavras = [
        proj.get("palavra_1"),
        proj.get("palavra_2"),
        proj.get("palavra_3"),
        proj.get("palavra_4"),
    ]
    for palavra in palavras:
        if not palavra:
            continue
        topico_id = upsert_topico(conn, palavra)
        if topico_id:
            vincular_projeto_topico(conn, projeto_id, topico_id)


def _parse_date(valor: str):
    try:
        from datetime import datetime
        return datetime.strptime(valor, "%d/%m/%Y").date()
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


# ---------------------------------------------------------------------------
# LOOP PRINCIPAL
# ---------------------------------------------------------------------------

conn = get_conn()
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

                projeto_id = salvar_projeto(conn, proj)
                if projeto_id:
                    salvar_palavras_chave(conn, projeto_id, proj)

            except Exception as e:
                print("Erro projeto:", e)
                conn.rollback()
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
    conn.close()
    driver.quit()