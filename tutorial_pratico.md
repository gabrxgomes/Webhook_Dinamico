# Tutorial Prático — Webhook Dinamico (em produção no Render)

Guia rápido e prático para **usar** o serviço que já está rodando em produção,
testando via **curl** e via **Postman**. Para instruções de deploy/configuração
do Render, veja [DOCUMENTATION.md](DOCUMENTATION.md) — este arquivo é só sobre
**como consumir o serviço que já está no ar**.

URL base em produção:
```
https://webhook-dinamico.onrender.com
```

---

## 1. URLs do serviço

| Finalidade                  | Método | URL                                                      |
|------------------------------|--------|-----------------------------------------------------------|
| Gerar um Bearer Token        | POST   | `https://webhook-dinamico.onrender.com/oauth/token`        |
| Receber webhook (Bearer)     | POST   | `https://webhook-dinamico.onrender.com/webhook/bearer`     |
| Receber webhook (Basic Auth) | POST   | `https://webhook-dinamico.onrender.com/webhook/basic`      |
| Health check (UptimeRobot)   | GET    | `https://webhook-dinamico.onrender.com/health`             |

---

## 2. Onde pegar suas credenciais

As credenciais reais (`CLIENT_ID`, `CLIENT_SECRET`, `JWT_SECRET_KEY`) ficam em:

**Render → seu serviço (`webhook-dinamico`) → aba Environment**

Nos exemplos abaixo, substitua:
- `SEU_CLIENT_ID` → valor de `CLIENT_ID` (ex.: `Dinamic_webhook_test`)
- `SEU_CLIENT_SECRET` → valor de `CLIENT_SECRET`

**Nunca** coloque o `CLIENT_SECRET` ou o `JWT_SECRET_KEY` em arquivos
versionados no GitHub — esse repositório é público. Use-os só localmente, em
requisições, ou nas configurações da plataforma que envia os webhooks.

---

## 3. Testando via cURL

### 3.1. Gerar um Bearer Token

O `/oauth/token` aceita credenciais de 3 formas — use a que for mais
conveniente:

**a) Basic Auth (header HTTP):**
```bash
curl -X POST https://webhook-dinamico.onrender.com/oauth/token \
  -u 'SEU_CLIENT_ID:SEU_CLIENT_SECRET'
```

**b) Corpo em JSON:**
```bash
curl -X POST https://webhook-dinamico.onrender.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id": "SEU_CLIENT_ID", "client_secret": "SEU_CLIENT_SECRET"}'
```

**c) Corpo form-encoded:**
```bash
curl -X POST https://webhook-dinamico.onrender.com/oauth/token \
  -d "client_id=SEU_CLIENT_ID&client_secret=SEU_CLIENT_SECRET"
```

Resposta esperada (`200`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Esse `access_token` é o **Bearer token**. Ele expira em `3600` segundos
(1 hora) — depois disso, repita esta chamada para gerar um novo.

### 3.2. Enviar um webhook de teste via Bearer Token

```bash
TOKEN="cole_aqui_o_access_token_recebido"

curl -X POST https://webhook-dinamico.onrender.com/webhook/bearer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event": "teste.manual", "origem": "tutorial_pratico"}'
```

Resposta esperada (`200`):
```json
{
  "status": "received",
  "auth_method": "bearer",
  "message": "Webhook received and authenticated via Bearer token",
  "token_subject": "SEU_CLIENT_ID",
  "received_at": "2026-06-22T20:26:08.481156+00:00"
}
```

### 3.3. Enviar um webhook de teste via Basic Auth

Não precisa gerar token antes — manda direto com Basic Auth:

```bash
curl -X POST https://webhook-dinamico.onrender.com/webhook/basic \
  -u 'SEU_CLIENT_ID:SEU_CLIENT_SECRET' \
  -H "Content-Type: application/json" \
  -d '{"event": "teste.manual", "origem": "tutorial_pratico"}'
```

Resposta esperada (`200`):
```json
{
  "status": "received",
  "auth_method": "basic",
  "message": "Webhook received and authenticated via HTTP Basic Authentication",
  "received_at": "2026-06-22T20:26:08.481156+00:00"
}
```

### 3.4. Verificar se o serviço está de pé

```bash
curl https://webhook-dinamico.onrender.com/health
```

Resposta esperada (`200`):
```json
{"status": "ok"}
```

### 3.5. Testando erros de propósito (para validar a segurança)

```bash
# client_secret errado -> 401
curl -i -X POST https://webhook-dinamico.onrender.com/oauth/token -u 'SEU_CLIENT_ID:secret-errado'

# token inválido/expirado -> 401
curl -i -X POST https://webhook-dinamico.onrender.com/webhook/bearer \
  -H "Authorization: Bearer token-invalido" -d '{}'

# sem nenhuma credencial -> 401
curl -i -X POST https://webhook-dinamico.onrender.com/webhook/basic -d '{}'
```

Todos devem retornar `401` com `{"error": ...}`.

---

## 4. Testando via Postman

### 4.1. Caminho rápido — importar a coleção pronta

O repositório já tem uma coleção pronta em
`postman/Webhook_Dinamico.postman_collection.json`.

1. Postman → **Import** → selecione esse arquivo.
2. Clique na coleção → aba **Variables** → ajuste:
   - `base_url` → `https://webhook-dinamico.onrender.com`
   - `client_id` → `SEU_CLIENT_ID`
   - `client_secret` → `SEU_CLIENT_SECRET`
   - `access_token` → deixe vazio (é preenchido automaticamente)
3. Rode as requisições nessa ordem:
   1. **1. Get Bearer Token** — `POST /oauth/token` com Basic Auth. Um script
      de teste já copia o `access_token` da resposta para a variável da
      coleção.
   2. **2. Send Webhook (Basic)** — `POST /webhook/basic`.
   3. **3. Send Webhook (Bearer)** — `POST /webhook/bearer`, já usa o token
      salvo no passo 1.
   4. **4. Health Check** — `GET /health`.

### 4.2. Caminho manual — montando as requisições você mesmo

**Requisição 1 — Gerar token**
- Método: `POST`
- URL: `https://webhook-dinamico.onrender.com/oauth/token`
- Authorization → tipo **Basic Auth** → Username = `SEU_CLIENT_ID`,
  Password = `SEU_CLIENT_SECRET`
- Send → copie o valor de `access_token` da resposta.

**Requisição 2 — Enviar webhook via Bearer**
- Método: `POST`
- URL: `https://webhook-dinamico.onrender.com/webhook/bearer`
- Authorization → tipo **Bearer Token** → cole o `access_token` copiado
  (⚠️ não confunda com `JWT_SECRET_KEY` — esse é só do servidor, nunca é
  enviado por quem chama o webhook)
- Body → raw → JSON → `{"event": "teste"}`
- Send → espera `200`.

**Requisição 3 — Enviar webhook via Basic Auth**
- Método: `POST`
- URL: `https://webhook-dinamico.onrender.com/webhook/basic`
- Authorization → tipo **Basic Auth** → mesmas credenciais
- Body → raw → JSON → `{"event": "teste"}`
- Send → espera `200`.

**Requisição 4 — Health check**
- Método: `GET`
- URL: `https://webhook-dinamico.onrender.com/health`
- Send → espera `200`, `{"status": "ok"}`.

---

## 5. Configurando em uma plataforma externa (ex.: ATS / sistema de RH)

Se a plataforma que vai enviar os webhooks tiver um formulário genérico de
"Webhook" com opções de autorização, use:

| Modo de autorização na plataforma | Campos a preencher |
|---|---|
| **Token dinâmico** (recomendado) | Token URL = `.../oauth/token`; Client ID = `SEU_CLIENT_ID`; Client Secret = `SEU_CLIENT_SECRET`; URL de destino = `.../webhook/bearer` |
| **Token estático** | Não suportado por este projeto — ele só gera tokens dinamicamente via `/oauth/token` |
| **Basic Auth direto** | Username = `SEU_CLIENT_ID`; Password = `SEU_CLIENT_SECRET`; URL de destino = `.../webhook/basic` |
| **Sem autorização** | Não suportado — os dois endpoints de webhook exigem autenticação |

⚠️ Erro comum: colocar a **URL de destino** como a raiz do serviço
(`https://webhook-dinamico.onrender.com/`) em vez de `/webhook/bearer` ou
`/webhook/basic`. A raiz não existe como rota e qualquer requisição ali
falha.

---

## 6. Vendo os webhooks recebidos

Render → seu serviço → aba **Logs**. Cada webhook aceito aparece assim:

```
============================================================
[2026-06-22 20:26:08] WEBHOOK RECEIVED [BEARER]
  Method      : POST
  Content-Type: application/json

  --- Body (JSON) ---
  {
    "event": "teste.manual",
    "origem": "tutorial_pratico"
  }
============================================================
```

Tentativas rejeitadas também aparecem, com o motivo:
```
[2026-06-22 20:26:08] UNAUTHORIZED (bearer) - invalid, expired, or missing token
[2026-06-22 20:26:08] TOKEN REQUEST REJECTED - invalid client_id/secret
```

---

## 7. Troubleshooting rápido

| Sintoma | Causa provável | Solução |
|---|---|---|
| `401` ao gerar token | `client_id`/`client_secret` errados | Confira os valores em Render → Environment |
| `401` ao chamar `/webhook/bearer` | Token expirado (dura 1h) ou usou o `JWT_SECRET_KEY` no lugar do `access_token` | Gere um token novo em `/oauth/token` e use o `access_token` retornado |
| `404` | URL de destino errada | Use `/webhook/bearer` ou `/webhook/basic`, nunca a raiz `/` |
| Primeira chamada lenta (~30s) | Plano free do Render "dorme" após inatividade | Normal; configure o UptimeRobot apontando para `/health` a cada 5 min para evitar isso |
