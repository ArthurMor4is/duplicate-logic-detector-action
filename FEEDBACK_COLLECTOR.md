# 📡 Feedback Collector - Servidor Simples

Servidor simples para coletar reações em tempo real dos comentários da Duplicate Logic Detector Action.

## 🚀 Instalação e Execução

### 1. Instalar Dependências

```bash
npm install
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp config.example .env

# Editar configurações
export PORT=3000
export WEBHOOK_SECRET="seu-webhook-secret-aqui"
export DATA_FILE="feedback-reactions.json"
```

### 3. Executar Servidor

```bash
# Produção
npm start

# Desenvolvimento (com auto-reload)
npm run dev
```

O servidor estará disponível em `http://localhost:3000`

## 🔧 Configuração do GitHub Webhook

1. Vá para as configurações do seu repositório
2. Clique em "Webhooks" → "Add webhook"
3. Configure:
   - **URL**: `https://seu-dominio.com/webhook`
   - **Content type**: `application/json`
   - **Secret**: O mesmo valor da variável `WEBHOOK_SECRET`
   - **Events**: Marque apenas "Issue comments"

## 📊 Endpoints Disponíveis

### `GET /` - Página Inicial
Mostra status do servidor e instruções básicas.

### `POST /webhook` - Webhook do GitHub
Recebe eventos do GitHub automaticamente. Não chamar manualmente.

### `GET /data` - Ver Dados Coletados
```bash
curl http://localhost:3000/data
```

Retorna lista de todos os comentários monitorados com suas reações.

### `GET /stats` - Estatísticas Resumidas
```bash
curl http://localhost:3000/stats
```

Retorna métricas como:
- Total de comentários
- Total de reações
- Score de satisfação
- Taxa de engajamento

### `POST /update-reactions` - Atualizar Reações Específicas
```bash
curl -X POST http://localhost:3000/update-reactions \
  -H "Content-Type: application/json" \
  -d '{"commentId": "123456", "token": "seu_github_token"}'
```

Atualiza as reações de um comentário específico.

### `POST /update-all` - Atualizar Todas as Reações
```bash
curl -X POST http://localhost:3000/update-all \
  -H "Content-Type: application/json" \
  -d '{"token": "seu_github_token"}'
```

Atualiza as reações de todos os comentários monitorados.

### `GET /health` - Status do Servidor
```bash
curl http://localhost:3000/health
```

Verifica se o servidor está funcionando.

## 📁 Estrutura de Dados

Os dados são salvos em JSON no formato:

```json
{
  "id": 123456,
  "timestamp": "2024-01-15T10:30:00Z",
  "repository": "owner/repo",
  "issue_number": 42,
  "comment_url": "https://github.com/owner/repo/pull/42#issuecomment-123456",
  "author": "developer1",
  "created_at": "2024-01-15T09:30:00Z",
  "body_preview": "## 🔍 Duplicate Logic Detection...",
  "reactions": [
    {
      "type": "+1",
      "user": "reviewer1",
      "created_at": "2024-01-15T10:35:00Z"
    }
  ],
  "stats": {
    "total": 3,
    "positive": 2,
    "negative": 1,
    "satisfaction": 67
  },
  "last_updated": "2024-01-15T11:00:00Z"
}
```

## 🎯 Como Funciona

1. **Detecção Automática**: O servidor monitora comentários criados via webhook
2. **Identificação**: Identifica comentários da Duplicate Logic Detector
3. **Coleta de Reações**: Busca reações via API do GitHub
4. **Armazenamento**: Salva dados em arquivo JSON
5. **Estatísticas**: Calcula métricas em tempo real

## 🔄 Fluxo de Trabalho

1. Usuário cria PR
2. Duplicate Logic Detector posta comentário
3. Webhook notifica servidor
4. Servidor registra comentário
5. Usuários reagem ao comentário (👍, 👎, ❤️, etc.)
6. Servidor atualiza reações periodicamente
7. Dados ficam disponíveis via API

## 📈 Métricas Coletadas

- **Total de comentários** monitorados
- **Reações por tipo** (+1, -1, heart, rocket, etc.)
- **Score de satisfação** (% reações positivas)
- **Taxa de engajamento** (% comentários com reações)
- **Usuários mais ativos**

## 🚀 Deploy

### Vercel (Serverless)
```bash
npm install -g vercel
vercel
```

### Heroku
```bash
git init
heroku create seu-app-name
git add .
git commit -m "Initial commit"
git push heroku main
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## 🔐 Segurança

- ✅ Verificação de assinatura do webhook
- ✅ Validação de entrada
- ✅ Rate limiting natural (delays entre requests)
- ✅ Não armazena tokens permanentemente

## 📝 Logs

O servidor produz logs detalhados:

```
🚀 Feedback Collector Server iniciado!
📡 Servidor rodando na porta: 3000
💾 Arquivo de dados: feedback-reactions.json
📨 Evento recebido: issue_comment
📝 Novo comentário da Duplicate Logic Detector detectado:
   Repo: owner/repo
   PR/Issue: #42
   Comentário ID: 123456
✅ Reações atualizadas para comentário 123456:
   Total: 3, Positivas: 2, Negativas: 1
   Satisfação: 67%
```

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça suas alterações
4. Teste localmente
5. Submeta um pull request

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.
