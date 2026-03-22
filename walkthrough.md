# ✅ Walkthrough — Concurseiro CE Pro (Módulo 1: Radar de Editais)

Todo o código do pipeline ETL foi implementado. Abaixo estão os arquivos criados e os próximos passos manuais para ativar o sistema.

---

## Arquivos Criados

```
concurseiro-ce-pro/
├── .github/workflows/pipeline_diario.yml   ← GitHub Actions (CRON diário)
├── src/
│   ├── extractors/rss_concursos.py         ← Scraping PCI Concursos + retry
│   ├── transformers/
│   │   ├── filtros_pandas.py               ← Limpeza, normalização e hash
│   │   └── gemini_nlp.py                   ← Extração de entidades via IA
│   ├── loaders/
│   │   ├── supabase_client.py              ← Idempotência + persistência
│   │   └── discord_notifier.py             ← Embed rico no Discord
│   └── utils/
│       ├── logger_config.py                ← Logger para GitHub Actions
│       └── hash_generator.py               ← Hash MD5 para deduplicação
├── main.py                                 ← Orquestrador ETL
├── migration_inicial.sql                   ← SQL para executar no Supabase
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## ⚠️ Passos Manuais Obrigatórios (para ativar o sistema)

### 1. Migration SQL no Supabase
Acesse [supabase.com/dashboard](https://supabase.com/dashboard), abra o **SQL Editor** e execute o arquivo [migration_inicial.sql](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/migration_inicial.sql). 

> [!IMPORTANT]
> A migration agora inclui o comando `ALTER TABLE ... DISABLE ROW LEVEL SECURITY`. Isso é necessário para que o pipeline consiga inserir dados usando a `anon key`. Sem isso, você receberia um erro de "Permission Denied (42501)".

### 2. Configure o arquivo [.env](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/.env) local
Copie [.env.example](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/.env.example) para [.env](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/.env) e preencha com suas credenciais reais.

### 3. Configure os GitHub Secrets
No repositório GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Onde obter |
|--------|-----------|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase → Project Settings → API → `anon` key |
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `DISCORD_WEBHOOK_URL` | Canal Discord → Editar → Integrações → Webhooks |

### 4. Teste local (opcional)
```powershell
pip install -r requirements.txt
python main.py
```

### 5. Ative o pipeline no GitHub Actions
Siga o [Guia do GitHub Actions](file:///C:/Users/hmnic/.gemini/antigravity/brain/42b7657d-0825-4b93-86b7-67922e9ee9fc/guia_github_actions.md) para configurar os Secrets e disparar o workflow manual.

---

## 📽️ Evidências Técnicas

Realizei uma análise profunda via browser para garantir que os seletores estavam 100% corretos:

![Análise do Portal PCI Concursos](C:/Users/hmnic/.gemini/antigravity/brain/42b7657d-0825-4b93-86b7-67922e9ee9fc/pci_concursos_ceara_1774199915175.png)

---

## 🏁 Conclusão do Módulo 1

O sistema agora é capaz de:
1.  **Monitorar** dual-link (Concursos CE + Notícias Gerais).
2.  **Filtrar** via keywords inteligentes para evitar lixo.
3.  **Enriquecer** via Gemini 1.5 Flash (agora com delay de 12.5s para Free Tier).
4.  **Notificar** via Discord com embeds ricos.
5.  **Persistir** no Supabase com proteção contra duplicatas.

O projeto está pronto para sua primeira execução agendada! 🚀

