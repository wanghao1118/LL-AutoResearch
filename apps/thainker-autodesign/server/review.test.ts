import assert from 'node:assert/strict';
import test from 'node:test';
import { latestRecordedDecision, parseMethodRevisionDecision, parseMethodRevisionProposal } from './review';

test('parses a bold Markdown Revision ID and the four Chinese approval sections', () => {
  const review = parseMethodRevisionProposal([
    '- **Revision ID:** `REV-C2-MATCHED-COVERAGE-01`',
    '## 审核背景',
    '原实验缺少同覆盖率比较，现有结果不能直接替代。',
    '## 具体修改方法',
    '固定参考方法并使用全新的三个种子重新验证。',
    '## 设计思路',
    '使用新输出避免根据已经看过的正式结果选择规则。',
    '## 实验验证',
    '六个新单元；不通过则保持原结果并收窄结论。',
  ].join('\n'), 'method_revision_limit: 2\napproved_method_revisions: 0');

  assert.equal(review?.revisionId, 'REV-C2-MATCHED-COVERAGE-01');
  assert.equal(review?.languageReady, true);
  assert.match(review?.background || '', /同覆盖率比较/);
  assert.match(review?.modification || '', /三个种子/);
});

test('blocks approval when the proposal has no complete Chinese summary', () => {
  const review = parseMethodRevisionProposal([
    '- **Revision ID:** `REV-ENGLISH-ONLY-01`',
    '## Triggering evidence',
    'The metric is missing.',
    '## One smallest proposed delta',
    'Run a new comparison.',
  ].join('\n'), '');

  assert.equal(review?.revisionId, 'REV-ENGLISH-ONLY-01');
  assert.equal(review?.languageReady, false);
  assert.match(review?.question || '', /暂不能批准/);
});

test('recovers the latest submitted decision for an interrupted backend run', () => {
  assert.deepEqual(latestRecordedDecision([
    { text: '任务已暂停，等待 Yes 或 No' },
    { text: '已记录人工决定：APPROVE_MINIMAL_METHOD_REVISION · REV-OLD-01' },
    { text: '已记录人工决定：APPROVE_MINIMAL_METHOD_REVISION · REV-C2-MATCHED-COVERAGE-01' },
  ]), {
    decision: 'APPROVE_MINIMAL_METHOD_REVISION',
    revisionId: 'REV-C2-MATCHED-COVERAGE-01',
  });
});

test('reads the current file decision without treating historical approval as active', () => {
  assert.deepEqual(parseMethodRevisionDecision([
    '# Method Revision Decision',
    '',
    '- **Revision ID:** `REV-C2-KZERO-02`',
    '- **Decision:** `REJECT_METHOD_REVISION`',
    '',
    '## 历史决定',
    '',
    '- `APPROVE_MINIMAL_METHOD_REVISION` was recorded earlier.',
  ].join('\n')), {
    revisionId: 'REV-C2-KZERO-02',
    decision: 'REJECT_METHOD_REVISION',
  });
});
