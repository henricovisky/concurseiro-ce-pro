# 🚀 Guia de Automação: GitHub Actions

Siga estes passos para que o projeto rode sozinho todo dia às **08:00 UTC** (05:00 Brasília).

---

## 1. Inicializar o Git e Enviar ao GitHub

No seu terminal (dentro da pasta do projeto), rode estes comandos:

```powershell
# 1. Inicializa o repositório
git init

# 2. Adiciona os arquivos (o .gitignore evitará o envio do .env e venv)
git add .

# 3. Faz o primeiro commit
git commit -m "feat: setup inicial do radar de editais"

# 4. Conecte ao seu repositório no GitHub (crie um repo vazio lá primeiro)
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git

# 5. Envia o código
git push -u origin main
```

---

## 2. Configurar os GitHub Secrets (Obrigatório)

O GitHub Actions não consegue ler seu arquivo [.env](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/.env) local. Você precisa cadastrar as chaves no painel do GitHub para que ele as use com segurança:

1. Vá no seu repositório no GitHub.
2. Clique em **Settings** (Configurações).
3. No menu lateral, vá em **Secrets and variables** -> **Actions**.
4. Clique em **New repository secret** e adicione estas **4 chaves** exatamente como abaixo:

| Nome do Secret | Valor para colar |
|----------------|------------------|
| `SUPABASE_URL` | Sua URL do Supabase |
| `SUPABASE_KEY` | Sua `anon` key do Supabase |
| `GEMINI_API_KEY` | Sua chave da API do Gemini |
| `DISCORD_WEBHOOK_URL` | Seu link REAL do Webhook do Discord |

---

## 3. Ativar e Testar o Workflow

Uma vez que o código subiu e os Secrets foram configurados:

1. Clique na aba **Actions** no topo do seu repositório GitHub.
2. Você verá o workflow: **🚀 Radar de Editais — Pipeline Diário**.
3. Clique nele e depois no botão **Run workflow** -> **Run workflow**.

Isso disparará o script imediatamente. Se tudo estiver certo, você receberá a notificação no Discord em alguns minutos!

---

## 💡 Como funciona o agendamento?

No arquivo [.github/workflows/pipeline_diario.yml](file:///d:/Documentos/00%20-%20Projetos/concurseiro-ce-pro/.github/workflows/pipeline_diario.yml), a linha:
`cron: "0 8 * * *"` 
Diz ao GitHub para rodar o script todos os dias às 08:00 (horário UTC). Você pode mudar esse horário editando este arquivo.
