#!/usr/bin/env node
/**
 * Servidor simples para coletar reações em tempo real dos comentários
 * da Duplicate Logic Detector Action
 */

const express = require('express');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

const app = express();
app.use(express.json({ limit: '10mb' }));

// Configuração
const PORT = process.env.PORT || 3000;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'your-webhook-secret-here';
const DATA_FILE = process.env.DATA_FILE || 'feedback-reactions.json';

// Armazenar dados em memória para acesso rápido
let reactionData = [];

/**
 * Verificar assinatura do webhook do GitHub
 */
function verifyGitHubSignature(payload, signature, secret) {
  if (!signature) return false;
  
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload, 'utf8').digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}

/**
 * Verificar se o comentário é da duplicate logic detector
 */
function isDuplicateDetectorComment(commentBody) {
  if (!commentBody) return false;
  
  return commentBody.includes('🔍 Duplicate Logic Detection') ||
         commentBody.includes('duplicate-logic-detector-comment-') ||
         commentBody.includes('Help us improve! React with');
}

/**
 * Salvar dados no arquivo
 */
async function saveData() {
  try {
    await fs.writeFile(DATA_FILE, JSON.stringify(reactionData, null, 2));
    console.log(`💾 Dados salvos: ${reactionData.length} entradas`);
  } catch (error) {
    console.error('❌ Erro ao salvar dados:', error.message);
  }
}

/**
 * Carregar dados existentes
 */
async function loadData() {
  try {
    const data = await fs.readFile(DATA_FILE, 'utf8');
    reactionData = JSON.parse(data);
    console.log(`📂 Dados carregados: ${reactionData.length} entradas`);
  } catch (error) {
    console.log('📝 Iniciando com dados vazios');
    reactionData = [];
  }
}

/**
 * Buscar reações de um comentário via API do GitHub
 */
async function fetchCommentReactions(owner, repo, commentId, token) {
  try {
    const response = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/issues/comments/${commentId}/reactions`,
      {
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'Duplicate-Logic-Detector-Feedback-Collector'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const reactions = await response.json();
    return reactions.map(reaction => ({
      type: reaction.content,
      user: reaction.user.login,
      created_at: reaction.created_at
    }));

  } catch (error) {
    console.error(`❌ Erro ao buscar reações do comentário ${commentId}:`, error.message);
    return null;
  }
}

/**
 * Processar comentário criado
 */
async function handleCommentCreated(payload) {
  const { comment, issue, repository } = payload;
  
  if (!isDuplicateDetectorComment(comment.body)) {
    return;
  }

  console.log(`📝 Novo comentário da Duplicate Logic Detector detectado:`);
  console.log(`   Repo: ${repository.full_name}`);
  console.log(`   PR/Issue: #${issue.number}`);
  console.log(`   Comentário ID: ${comment.id}`);

  // Adicionar entrada inicial (sem reações ainda)
  const entry = {
    id: comment.id,
    timestamp: new Date().toISOString(),
    repository: repository.full_name,
    issue_number: issue.number,
    comment_url: comment.html_url,
    author: comment.user.login,
    created_at: comment.created_at,
    body_preview: comment.body.substring(0, 100) + '...',
    reactions: [],
    last_updated: new Date().toISOString()
  };

  // Verificar se já existe
  const existingIndex = reactionData.findIndex(item => item.id === comment.id);
  if (existingIndex >= 0) {
    reactionData[existingIndex] = entry;
  } else {
    reactionData.push(entry);
  }

  await saveData();
}

/**
 * Atualizar reações de um comentário específico
 */
async function updateCommentReactions(commentId, token) {
  const entry = reactionData.find(item => item.id === commentId);
  if (!entry) {
    console.log(`⚠️ Comentário ${commentId} não encontrado nos dados`);
    return false;
  }

  const [owner, repo] = entry.repository.split('/');
  const reactions = await fetchCommentReactions(owner, repo, commentId, token);
  
  if (reactions) {
    entry.reactions = reactions;
    entry.last_updated = new Date().toISOString();
    
    // Calcular estatísticas simples
    const positive = reactions.filter(r => ['+1', 'heart', 'rocket', 'hooray'].includes(r.type));
    const negative = reactions.filter(r => ['-1', 'confused'].includes(r.type));
    
    entry.stats = {
      total: reactions.length,
      positive: positive.length,
      negative: negative.length,
      satisfaction: reactions.length > 0 ? 
        Math.round((positive.length / reactions.length) * 100) : 0
    };

    console.log(`✅ Reações atualizadas para comentário ${commentId}:`);
    console.log(`   Total: ${entry.stats.total}, Positivas: ${entry.stats.positive}, Negativas: ${entry.stats.negative}`);
    console.log(`   Satisfação: ${entry.stats.satisfaction}%`);

    await saveData();
    return true;
  }

  return false;
}

// ================================
// ENDPOINTS DO SERVIDOR
// ================================

/**
 * Webhook principal do GitHub
 */
app.post('/webhook', async (req, res) => {
  const signature = req.headers['x-hub-signature-256'];
  const event = req.headers['x-github-event'];
  const payload = JSON.stringify(req.body);

  // Verificar assinatura
  if (!verifyGitHubSignature(payload, signature, WEBHOOK_SECRET)) {
    console.log('❌ Assinatura do webhook inválida');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  console.log(`📨 Evento recebido: ${event}`);

  try {
    if (event === 'issue_comment' && req.body.action === 'created') {
      await handleCommentCreated(req.body);
    }
    
    res.status(200).json({ message: 'OK' });
  } catch (error) {
    console.error('❌ Erro processando webhook:', error.message);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

/**
 * Atualizar reações manualmente
 * POST /update-reactions
 * Body: { commentId: "123456", token: "github_token" }
 */
app.post('/update-reactions', async (req, res) => {
  const { commentId, token } = req.body;

  if (!commentId || !token) {
    return res.status(400).json({ 
      error: 'commentId e token são obrigatórios' 
    });
  }

  const success = await updateCommentReactions(parseInt(commentId), token);
  
  if (success) {
    const entry = reactionData.find(item => item.id === parseInt(commentId));
    res.json({ 
      success: true, 
      comment: entry 
    });
  } else {
    res.status(404).json({ 
      error: 'Comentário não encontrado ou erro na API' 
    });
  }
});

/**
 * Atualizar todas as reações
 * POST /update-all
 * Body: { token: "github_token" }
 */
app.post('/update-all', async (req, res) => {
  const { token } = req.body;

  if (!token) {
    return res.status(400).json({ error: 'token é obrigatório' });
  }

  console.log(`🔄 Atualizando reações de ${reactionData.length} comentários...`);
  
  let updated = 0;
  for (const entry of reactionData) {
    const success = await updateCommentReactions(entry.id, token);
    if (success) updated++;
    
    // Pequeno delay para não sobrecarregar a API
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  res.json({ 
    message: `Atualização concluída: ${updated}/${reactionData.length} comentários atualizados` 
  });
});

/**
 * Ver dados coletados
 * GET /data
 */
app.get('/data', (req, res) => {
  const summary = reactionData.map(entry => ({
    id: entry.id,
    repository: entry.repository,
    issue_number: entry.issue_number,
    author: entry.author,
    created_at: entry.created_at,
    last_updated: entry.last_updated,
    stats: entry.stats || { total: 0, positive: 0, negative: 0, satisfaction: 0 },
    comment_url: entry.comment_url
  }));

  res.json({
    total_comments: reactionData.length,
    comments: summary
  });
});

/**
 * Estatísticas resumidas
 * GET /stats
 */
app.get('/stats', (req, res) => {
  const totalComments = reactionData.length;
  const commentsWithReactions = reactionData.filter(entry => 
    entry.stats && entry.stats.total > 0
  ).length;

  const totalReactions = reactionData.reduce((sum, entry) => 
    sum + (entry.stats?.total || 0), 0
  );

  const totalPositive = reactionData.reduce((sum, entry) => 
    sum + (entry.stats?.positive || 0), 0
  );

  const totalNegative = reactionData.reduce((sum, entry) => 
    sum + (entry.stats?.negative || 0), 0
  );

  const overallSatisfaction = totalReactions > 0 ? 
    Math.round((totalPositive / totalReactions) * 100) : 0;

  res.json({
    total_comments: totalComments,
    comments_with_reactions: commentsWithReactions,
    total_reactions: totalReactions,
    positive_reactions: totalPositive,
    negative_reactions: totalNegative,
    overall_satisfaction: overallSatisfaction,
    engagement_rate: totalComments > 0 ? 
      Math.round((commentsWithReactions / totalComments) * 100) : 0
  });
});

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    data_entries: reactionData.length
  });
});

/**
 * Página inicial com instruções
 */
app.get('/', (req, res) => {
  res.send(`
    <h1>🔍 Duplicate Logic Detector - Feedback Collector</h1>
    <p>Servidor para coleta de reações em tempo real</p>
    
    <h2>Endpoints:</h2>
    <ul>
      <li><code>POST /webhook</code> - Webhook do GitHub</li>
      <li><code>POST /update-reactions</code> - Atualizar reações de um comentário</li>
      <li><code>POST /update-all</code> - Atualizar todas as reações</li>
      <li><code>GET /data</code> - Ver dados coletados</li>
      <li><code>GET /stats</code> - Estatísticas resumidas</li>
      <li><code>GET /health</code> - Status do servidor</li>
    </ul>
    
    <h2>Status:</h2>
    <p>Comentários monitorados: <strong>${reactionData.length}</strong></p>
    <p>Arquivo de dados: <strong>${DATA_FILE}</strong></p>
  `);
});

// ================================
// INICIALIZAÇÃO DO SERVIDOR
// ================================

async function startServer() {
  await loadData();
  
  app.listen(PORT, () => {
    console.log('🚀 Feedback Collector Server iniciado!');
    console.log(`📡 Servidor rodando na porta: ${PORT}`);
    console.log(`💾 Arquivo de dados: ${DATA_FILE}`);
    console.log(`🔐 Webhook secret configurado: ${WEBHOOK_SECRET ? 'Sim' : 'Não'}`);
    console.log('');
    console.log('📋 Configuração do Webhook GitHub:');
    console.log(`   URL: http://seu-dominio.com/webhook`);
    console.log(`   Content type: application/json`);
    console.log(`   Secret: ${WEBHOOK_SECRET}`);
    console.log(`   Events: Issue comments`);
    console.log('');
    console.log('🌐 Acesse http://localhost:' + PORT + ' para ver o status');
  });
}

// Iniciar servidor
startServer().catch(console.error);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('🛑 Parando servidor...');
  await saveData();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('🛑 Parando servidor...');
  await saveData();
  process.exit(0);
});
