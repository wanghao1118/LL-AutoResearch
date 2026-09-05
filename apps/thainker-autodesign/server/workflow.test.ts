import assert from 'node:assert/strict';
import test from 'node:test';
import { needsAuditReviewPreparation } from './workflow';

test('routes an integrity-audit failure to one human-review preparation turn', () => {
  assert.equal(needsAuditReviewPreparation('INTEGRITY_AUDIT_FAIL', 'failed', false), true);
});

test('does not loop after review preparation already failed once', () => {
  assert.equal(needsAuditReviewPreparation('INTEGRITY_AUDIT_FAIL', 'failed', true), false);
});

test('does not turn ordinary execution failures into scientific approvals', () => {
  assert.equal(needsAuditReviewPreparation('EXECUTION_IN_PROGRESS', 'failed', false), false);
});
