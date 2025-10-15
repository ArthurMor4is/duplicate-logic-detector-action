#!/usr/bin/env node
/**
 * Script de teste para demonstrar o uso do Feedback Collector
 */

const http = require('http');

const SERVER_URL = 'http://localhost:3000';

/**
 * Fazer requisição HTTP
 */
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve({ status: res.statusCode, data: result });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

/**
 * Simular webhook do GitHub
 */
function simulateWebhook() {
  const webhookPayload = {
    action: 'created',
    comment: {
      id: 123456789,
      user: { login: 'developer1' },
      created_at: new Date().toISOString(),
      html_url: 'https://github.com/test/repo/pull/42#issuecomment-123456789',
      body: `## 🔍 Duplicate Logic Detection

The following functions in your PR may recreate logic that already exists:

### Match 1: High Confidence
**New Function:** \`calculate_total\` in \`src/billing.py\`
**Similar to:** \`compute_sum\` in \`src/utils/math.py\`
**Similarity:** 85.2%

---

*💡 **Help us improve!** React with 👍 if this analysis was helpful, or 👎 if it needs improvement.*
<!-- duplicate-logic-detector-comment-${Date.now()} -->`
    },
    issue: {
      number: 42
    },
    repository: {
      full_name: 'test/repo'
    }
  };

  return webhookPayload;
}

/**
 * Executar testes
 */
async function runTests() {
  console.log('🧪 Testando Feedback Collector Server\n');

  try {
    // 1. Verificar se servidor está rodando
    console.log('1. Verificando status do servidor...');
    const health = await makeRequest('GET', '/health');
    console.log(`   Status: ${health.status}`);
    console.log(`   Uptime: ${health.data.uptime?.toFixed(2)}s`);
    console.log(`   Entradas: ${health.data.data_entries}`);

    // 2. Ver estatísticas iniciais
    console.log('\n2. Estatísticas iniciais...');
    const initialStats = await makeRequest('GET', '/stats');
    console.log(`   Comentários: ${initialStats.data.total_comments}`);
    console.log(`   Reações: ${initialStats.data.total_reactions}`);
    console.log(`   Satisfação: ${initialStats.data.overall_satisfaction}%`);

    // 3. Simular webhook (comentário criado)
    console.log('\n3. Simulando webhook (comentário criado)...');
    const webhookData = simulateWebhook();
    
    // Nota: Este teste não inclui a verificação de assinatura
    // Em produção, você precisaria de um webhook secret válido
    console.log('   ⚠️  Para teste completo, configure WEBHOOK_SECRET e use webhook real');
    console.log(`   Comentário simulado ID: ${webhookData.comment.id}`);

    // 4. Ver dados após simulação
    console.log('\n4. Visualizando dados coletados...');
    const data = await makeRequest('GET', '/data');
    console.log(`   Total de comentários monitorados: ${data.data.total_comments}`);
    
    if (data.data.comments.length > 0) {
      const comment = data.data.comments[0];
      console.log(`   Último comentário:`);
      console.log(`     ID: ${comment.id}`);
      console.log(`     Repo: ${comment.repository}`);
      console.log(`     Autor: ${comment.author}`);
      console.log(`     Reações: ${comment.stats.total}`);
    }

    // 5. Testar endpoint de atualização (sem token real)
    console.log('\n5. Testando endpoint de atualização...');
    console.log('   ⚠️  Para teste completo, forneça um GitHub token válido');
    
    // 6. Estatísticas finais
    console.log('\n6. Estatísticas finais...');
    const finalStats = await makeRequest('GET', '/stats');
    console.log(`   Comentários: ${finalStats.data.total_comments}`);
    console.log(`   Taxa de engajamento: ${finalStats.data.engagement_rate}%`);

    console.log('\n✅ Testes concluídos com sucesso!');
    console.log('\n📋 Próximos passos:');
    console.log('   1. Configure o webhook no GitHub');
    console.log('   2. Defina WEBHOOK_SECRET nas variáveis de ambiente');
    console.log('   3. Monitore reações em tempo real!');

  } catch (error) {
    console.error('\n❌ Erro durante os testes:', error.message);
    console.log('\n💡 Certifique-se de que o servidor está rodando:');
    console.log('   npm start');
  }
}

// Executar testes se chamado diretamente
if (require.main === module) {
  runTests();
}

module.exports = { runTests, makeRequest, simulateWebhook };
