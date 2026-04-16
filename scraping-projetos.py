from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()

BASE_URL = "https://portal.ufsm.br/projetos/publico/projetos/list.html"
driver.get(BASE_URL)

wait = WebDriverWait(driver, 10)


# 👉 clicar no botão pesquisar (CORRETO)
def clicar_pesquisar():
    try:
        botao = wait.until(EC.element_to_be_clickable((By.ID, "search-btn")))
        botao.click()

        # espera tabela carregar
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    except Exception as e:
        print("❌ Erro ao clicar pesquisar:", e)


# 👉 ir pra página N
def ir_para_pagina(numero):
    for _ in range(numero - 1):
        try:
            next_li = wait.until(EC.presence_of_element_located((By.ID, "next_1")))

            if "disabled" in next_li.get_attribute("class"):
                return

            next_button = next_li.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", next_button)

            time.sleep(2)

        except:
            break


pagina = 1

# 🔥 primeira busca
clicar_pesquisar()

while True:
    print(f"\n=== Página {pagina} ===")

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    except:
        print("⚠️ Tabela não carregou")
        break

    linhas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    if not linhas:
        print("⚠️ Nenhuma linha encontrada")
        break

    projetos = []

    # 👉 coleta dados + links
    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")

        if len(colunas) < 6:
            continue

        try:
            link = linha.find_element(By.CSS_SELECTOR, "a[title='Abrir']")
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

    # 👉 entra nos detalhes
    for proj in projetos:
        try:
            driver.get(proj["url"])

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # resumo
            try:
                resumo = driver.find_element(
                    By.XPATH, "//span[text()='Resumo']/following::span[1]"
                ).text
            except:
                resumo = ""

            # coordenador
            coordenador = ""
            try:
                participantes = driver.find_elements(
                    By.CSS_SELECTOR, "#paginationWrapperParticipantes tbody tr"
                )

                for p in participantes:
                    tds = p.find_elements(By.TAG_NAME, "td")

                    if len(tds) >= 4 and "Coordenador" in tds[3].text:
                        coordenador = tds[2].text
                        break
            except:
                pass

            print({
                "numero": proj["numero"],
                "titulo": proj["titulo"],
                "inicio": proj["inicio"],
                "fim": proj["fim"],
                "situacao": proj["situacao"],
                "coordenador": coordenador,
                "resumo_len": len(resumo)
            })

            # 🔙 volta pra lista limpa
            driver.get(BASE_URL)

            clicar_pesquisar()
            ir_para_pagina(pagina)

        except Exception as e:
            print("❌ Erro no projeto:", e)
            driver.get(BASE_URL)
            clicar_pesquisar()
            ir_para_pagina(pagina)

    # 👉 próxima página
    try:
        next_li = wait.until(EC.presence_of_element_located((By.ID, "next_1")))

        if "disabled" in next_li.get_attribute("class"):
            print("🏁 Última página")
            break

        next_button = next_li.find_element(By.TAG_NAME, "a")
        driver.execute_script("arguments[0].click();", next_button)

        pagina += 1
        time.sleep(3)

    except Exception as e:
        print("❌ Erro ao trocar página:", e)
        break

driver.quit()
