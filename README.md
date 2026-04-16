# 🕷️ Scraper de Projetos UFSM

Script em Python utilizando **Selenium** para coletar dados públicos de projetos da UFSM diretamente do portal institucional.

---

## 📌 O que esse scraper faz

O bot navega automaticamente pelo site e coleta:

* Número do projeto
* Título
* Data de início
* Data de fim
* Situação
* Coordenador
* Resumo (armazenado, não exibido completo)

Ele percorre **todas as páginas**, acessa o detalhe de cada projeto e extrai as informações relevantes.

---

## ⚙️ Tecnologias utilizadas

* Python 3
* Selenium
* Google Chrome + ChromeDriver automático

---

## 🚀 Como rodar

### 1. Instalar dependências

```bash
pip install selenium
```

---

### 2. Executar o script

```bash
python nome_do_arquivo.py
```

---

## 🧠 Como o bot funciona

1. Acessa a página de projetos
2. Clica no botão **Pesquisar**
3. Percorre a tabela de resultados
4. Para cada linha:

   * Abre o detalhe do projeto
   * Extrai os dados
   * Volta para a lista
   * Clica novamente em **Pesquisar**
   * Volta para a página correta
5. Avança para a próxima página
6. Repete até o fim

---

## ⚠️ Problemas tratados

* ✔️ Paginação dinâmica (botão "Próxima página")
* ✔️ Recarregamento da tabela após voltar
* ✔️ Evita erro de índice (`IndexError`)
* ✔️ Evita erro de elemento não encontrado
* ✔️ Sincronização com `sleep` para evitar carregamento incompleto

---

## 📊 Exemplo de saída

```json
{
  "numero": "065298",
  "titulo": "Efeitos das Práticas Integrativas...",
  "inicio": "03/08/2026",
  "fim": "31/07/2030",
  "situacao": "Em andamento",
  "coordenador": "CAROLINA LISBOA MEZZOMO",
  "resumo_len": 2242
}
```

---

## 💾 Próximos passos (melhorias)

* Salvar dados em banco (PostgreSQL / MySQL)
* Exportar para CSV ou JSON
* Rodar em loop automático (cron job)
* Usar `WebDriverWait` ao invés de `sleep`
* Paralelizar coleta (mais avançado)

---

## ⚡ Observações

* O site usa carregamento dinâmico → por isso Selenium é necessário
* Sempre que o bot volta da página de detalhe, é obrigatório clicar novamente em **Pesquisar**
* O script simula um usuário real navegando

---

## 🧑‍💻 Autor

Bruno 🚀

---
