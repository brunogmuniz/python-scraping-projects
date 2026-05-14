# Scraper de Projetos UFSM

Script em Python usando Selenium para coletar dados públicos dos projetos diretamente do portal da UFSM.

---

## O que ele faz

O bot navega pelo site e coleta:

- Número do projeto  
- Título  
- Data de início  
- Data de fim  
- Situação  
- Coordenador  
- Resumo (armazenado, não exibido completo)

Ele percorre todas as páginas, entra no detalhe de cada projeto e extrai as informações.

---

## Tecnologias

- Python 3  
- Selenium  
- Google Chrome + ChromeDriver  

---

## Como rodar

### 1. Instalar dependências
pip install selenium

### 2. Executar
python nome_do_arquivo.py

---

## Como funciona

Fluxo do script:

1. Acessa a página de projetos  
2. Clica em "Pesquisar"  
3. Percorre a tabela de resultados  
4. Para cada projeto:
   - Abre o detalhe  
   - Extrai os dados  
   - Volta para a lista  
   - Clica em "Pesquisar" novamente  
   - Retorna para a página correta  
5. Avança para a próxima página  
6. Repete até o final  

---

## Problemas tratados

- Paginação (botão "Próxima página")  
- Recarregamento da tabela ao voltar  
- Evita erro de índice (IndexError)  
- Evita erro de elemento não encontrado  
- Uso de sleep para evitar problemas de carregamento  

---

## Exemplo de saída

{
  "numero": "065298",
  "titulo": "Efeitos das Práticas Integrativas...",
  "inicio": "03/08/2026",
  "fim": "31/07/2030",
  "situacao": "Em andamento",
  "coordenador": "AUTOR DO PROJETO",
  "resumo_len": 2242
}

---

## Possíveis melhorias

- Salvar dados em banco (PostgreSQL / MySQL)  
- Exportar para CSV ou JSON  
- Rodar automaticamente (cron job)  
- Substituir sleep por WebDriverWait  
- Paralelizar a coleta  

---

## Observações

- O site utiliza carregamento dinâmico, por isso o uso de Selenium  
- Sempre que o bot volta da página de detalhe, é necessário clicar novamente em "Pesquisar"  
- O script simula a navegação de um usuário  

---

## Autor
<img width="900" height="774" alt="projetos" src="https://github.com/user-attachments/assets/6e641827-9007-4316-a0a1-ffc10f4fa5a4" />

Bruno Munizz
