# 🏠 Concurseiro CE Pro — Módulo 1: Radar de Editais

[![Pipeline Diário](https://github.com/SEU_USUARIO/concurseiro-ce-pro/actions/workflows/pipeline_diario.yml/badge.svg)](https://github.com/SEU_USUARIO/concurseiro-ce-pro/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Supabase](https://img.shields.io/badge/database-Supabase-green.svg)](https://supabase.com/)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini_Flash-orange.svg)](https://aistudio.google.com/)

O **Concurseiro CE Pro** é um ecossistema de ferramentas inteligentes projetado para concurseiros do Ceará. Este repositório contém o **Módulo 1: Radar de Editais**, um pipeline ETL (Extract, Transform, Load) serverless que monitora, processa e notifica novos editais de concursos públicos no estado do Ceará de forma 100% automatizada.

---

## 🎯 Objetivos do Projeto

O Radar de Editais automatiza as tarefas repetitivas de busca por novas oportunidades:
- **Extração multi-fonte:** Coleta dados em tempo real do portal PCI Concursos (Ceará e Notícias Gerais).
- **Inteligência Artificial:** Utiliza o Google Gemini para extrair informações estruturadas (salário, vagas, data de prova) a partir de títulos brutos.
- **Idempotência:** Garante que o mesmo edital nunca seja processado ou notificado duas vezes.
- **Notificação em Tempo Real:** Envia alertas formatados (Rich Embeds) para canais do Discord.

---

## 🏗️ Arquitetura e Tecnologias

O sistema segue uma arquitetura modular baseada em camadas:

1.  **Extração (`extractors`):** Scraping HTML resiliente com `requests`, `BeautifulSoup` e `tenacity` (retry/backoff).
2.  **Transformação (`transformers`):**
    -   **Limpeza:** `pandas` para normalização de dados e tratamento de duplicatas locais.
    -   **Enriquecimento:** `google-generativeai` (Gemini 1.5 Flash) para extração de entidades via NLP.
3.  **Carga (`loaders`):**
    -   **Banco de Dados:** `supabase-py` (PostgreSQL) para persistência e controle de estado.
    -   **Notificação:** Discord Webhooks para entrega de mensagens.
4.  **Orquestração:** GitHub Actions rodando via CRON diário.

---

## 🚀 Como Começar

### Pré-requisitos
- Python 3.10 ou superior.
- Uma conta no [Supabase](https://supabase.com/).
- Uma chave de API no [Google AI Studio](https://aistudio.google.com/).
- Um Webhook de um canal do Discord.

### Instalação Local
1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/SEU_USUARIO/concurseiro-ce-pro.git
    cd concurseiro-ce-pro
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate  # Windows
    source venv/bin/activate # Linux/Mac
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração de Ambiente:**
    -   Copie o arquivo `.env.example` para `.env`.
    -   Preencha as variáveis com suas credenciais.

5.  **Setup do Banco de Dados:**
    -   Execute o script `migration_inicial.sql` no SQL Editor do seu projeto Supabase.

---

## 🤖 Automação via GitHub Actions

Para que o radar funcione sozinho todos os dias:
1.  Envie o código para o seu repositório GitHub.
2.  Configure os **Actions Secrets** no painel do GitHub (`SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`, `DISCORD_WEBHOOK_URL`).
3.  O workflow em `.github/workflows/pipeline_diario.yml` cuidará do resto.

> Confira o [Guia Detalhado do GitHub Actions](file:///C:/Users/hmnic/.gemini/antigravity/brain/42b7657d-0825-4b93-86b7-67922e9ee9fc/guia_github_actions.md) para mais detalhes.

---

## 📂 Estrutura do Projeto

```text
├── .github/workflows/      # Agendamento diário (GitHub Actions)
├── src/
│   ├── extractors/         # Scraping do PCI Concursos
│   ├── transformers/       # Limpeza Pandas e Enriquecimento Gemini
│   ├── loaders/            # Upload Supabase e Notificação Discord
│   ├── utils/              # Loggers e Geradores de Hash
│   └── __init__.py
├── main.py                 # Orquestrador principal (CLI)
├── migration_inicial.sql   # Schema do banco de dados
├── requirements.txt        # Dependências do projeto
└── .env.example            # Template de variáveis de ambiente
```

---

## 🛠️ Comandos Úteis

-   **Executar pipeline manualmente:** `python main.py`
-   **Executar incluindo seção de notícias:** `python main.py --com-noticias`

---

## 🗺️ Roadmap e Próximos Passos

- [x] Módulo 1: Radar de Editais (PCI Concursos).
- [ ] Módulo 2: Vigilante de Diários Oficiais (DOE-CE e DOU).
- [ ] Dashboards de estatísticas via Supabase.
- [ ] Filtros personalizados por nível de escolaridade.

---

## 📝 Licença
Este projeto é de uso pessoal e educacional. Sinta-se à vontade para adaptar para seu estado ou necessidade!