import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

BASE_URL = "https://portal.ufsm.br/projetos/publico/projetos/list.html"

driver.get(BASE_URL)

wait = WebDriverWait(driver, 10)


def clicar_pesquisar():
    try:
        botao = wait.until(
            EC.element_to_be_clickable((By.ID, "search-btn"))
        )

        driver.execute_script(
            "arguments[0].click();",
            botao
        )

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table tbody tr")
            )
        )

    except Exception as e:
        print("Erro ao pesquisar:", e)


def ir_para_pagina(numero):
    for _ in range(numero - 1):
        try:
            next_li = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "next_1")
                )
            )

            if "disabled" in next_li.get_attribute("class"):
                return

            next_button = next_li.find_element(By.TAG_NAME, "a")

            driver.execute_script(
                "arguments[0].click();",
                next_button
            )

            time.sleep(2)

        except:
            return


def buscar_campo_por_label(label):
    """
    Busca um campo baseado no texto da label
    Exemplo: Resumo, Palavra-chave 1, etc
    """

    try:
        elemento = driver.find_element(
            By.XPATH,
            f"//span[text()='{label}']/following-sibling::span"
        )

        return elemento.text.strip()

    except:
        return ""


def buscar_classificacoes():
    classificacao_cnpq = ""
    linha_pesquisa = ""
    tipo_orientacao = ""

    try:
        linhas = driver.find_elements(
            By.CSS_SELECTOR,
            ".panel-content .table .tbody .tr"
        )

        for linha in linhas:

            colunas = linha.find_elements(
                By.CSS_SELECTOR,
                ".td"
            )

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

    except:
        pass

    return {
        "classificacao_cnpq": classificacao_cnpq,
        "linha_pesquisa": linha_pesquisa,
        "tipo_orientacao": tipo_orientacao
    }


pagina = 1

clicar_pesquisar()

while True:

    print(f"\n=== Página {pagina} ===")

    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table tbody tr")
            )
        )
    except:
        break

    linhas = driver.find_elements(
        By.CSS_SELECTOR,
        "table tbody tr"
    )

    if not linhas:
        break

    projetos = []

    # pega links da página
    for linha in linhas:

        colunas = linha.find_elements(
            By.TAG_NAME,
            "td"
        )

        if len(colunas) < 6:
            continue

        try:
            link = linha.find_element(
                By.CSS_SELECTOR,
                "a[title='Abrir']"
            )

            url = link.get_attribute("href")

            projetos.append({
                "numero": colunas[1].text,
                "titulo": colunas[2].text,
                "inicio": colunas[3].text,
                "fim": colunas[4].text,
                "situacao": colunas[5].text,
                "url": url
            })

        except:
            continue

    # entra em cada projeto
    for proj in projetos:

        try:

            driver.get(proj["url"])

            wait.until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "body")
                )
            )

            # resumo
            resumo = buscar_campo_por_label("Resumo")

            # palavras-chave
            palavra1 = buscar_campo_por_label("Palavra-chave 1")
            palavra2 = buscar_campo_por_label("Palavra-chave 2")
            palavra3 = buscar_campo_por_label("Palavra-chave 3")
            palavra4 = buscar_campo_por_label("Palavra-chave 4")

            # classificações
            classificacoes = buscar_classificacoes()

            # coordenador
            coordenador = ""

            try:

                participantes = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#paginationWrapperParticipantes tbody tr"
                )

                for participante in participantes:

                    tds = participante.find_elements(
                        By.TAG_NAME,
                        "td"
                    )

                    if len(tds) >= 4:

                        if "Coordenador" in tds[3].text:
                            coordenador = tds[2].text.strip()
                            break

            except:
                pass

            resultado = {
                "numero": proj["numero"],
                "titulo": proj["titulo"],
                "inicio": proj["inicio"],
                "fim": proj["fim"],
                "situacao": proj["situacao"],

                "coordenador": coordenador,

                "classificacao_cnpq": classificacoes["classificacao_cnpq"],
                "linha_pesquisa": classificacoes["linha_pesquisa"],
                "tipo_orientacao": classificacoes["tipo_orientacao"],

                "palavra_1": palavra1,
                "palavra_2": palavra2,
                "palavra_3": palavra3,
                "palavra_4": palavra4,

                "resumo_len": len(resumo)
            }

            print(resultado)

            # voltar para lista
            driver.get(BASE_URL)

            clicar_pesquisar()

            ir_para_pagina(pagina)

        except Exception as e:

            print("Erro projeto:", e)

            driver.get(BASE_URL)

            clicar_pesquisar()

            ir_para_pagina(pagina)

    # próxima página
    try:

        next_li = wait.until(
            EC.presence_of_element_located(
                (By.ID, "next_1")
            )
        )

        if "disabled" in next_li.get_attribute("class"):
            break

        next_button = next_li.find_element(
            By.TAG_NAME,
            "a"
        )

        driver.execute_script(
            "arguments[0].click();",
            next_button
        )

        pagina += 1

        time.sleep(3)

    except:
        break


driver.quit()