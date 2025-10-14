// Post duplicate logic detection results as PR comment
// This script reads the markdown report and posts it as a GitHub comment

const fs = require('fs');

module.exports = async ({github, context, core}) => {
  try {
    const reportPath = 'duplicate-logic-report.md';
    
    if (!fs.existsSync(reportPath)) {
      core.warning('No markdown report found to post');
      return;
    }
    
    const report = fs.readFileSync(reportPath, 'utf8');
    
    if (!report.trim()) {
      core.warning('Markdown report is empty');
      return;
    }
    
    // Post the comment
    await github.rest.issues.createComment({
      issue_number: context.payload.pull_request?.number || process.env.PR_NUMBER,
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: report
    });
    
    core.info('✅ Posted duplicate logic detection results to PR');
    
  } catch (error) {
    core.error(`❌ Error posting comment: ${error.message}`);
    // Don't fail the action if commenting fails
  }
};
