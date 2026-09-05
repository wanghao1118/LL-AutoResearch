import assert from 'node:assert/strict';
import test from 'node:test';
import { deriveFormalProgress, mergeFormalProgress, type FormalProgress } from './progress';

test('derives the verified formal snapshot from artifacts without relying on UI messages', () => {
  const progress = deriveFormalProgress([
    {
      stage: 'validate_training',
      expected_cell_count: 36,
      observed_cell_count: 36,
      pass_cell_count: 36,
    },
    {
      stage: 'M1_prediction',
      expected_total_cell_count: 36,
      observed_total_cell_count: 36,
      pass_total_cell_count: 36,
    },
    { stage: 'M1_mask', status: 'NINTH_PAIR_PASS', completed_m1_mask_cells: 18 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Current stage | EXECUTION_IN_PROGRESS |',
    '| Primary result | partial only; 18/30 M1 mask cells complete and validated |',
    '| 22 | EXECUTION_IN_PROGRESS | EXECUTION_IN_PROGRESS | results | 18/30 complete | 启动 pair 10：`mtl_global/17` 与 `/29` |',
  ].join('\n'));

  assert.deepEqual(progress, {
    mode: 'formal_v1',
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 18, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: 'M1 遮挡实验',
    currentUnits: ['mtl_global/17', 'mtl_global/29'],
    currentPair: 10,
    maskPair: 10,
  });
});

test('keeps the last verified counts when a later artifact read is missing or older', () => {
  const previous: FormalProgress = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 18, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: 'M1 遮挡实验',
    currentUnits: ['mtl_global/17', 'mtl_global/29'],
    currentPair: 10,
    maskPair: 10,
  };
  const stale: FormalProgress = {
    training: null,
    prediction: { completed: 32, total: 36 },
    masking: { completed: 14, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: null,
    currentUnits: [],
    currentPair: 8,
    maskPair: 8,
  };

  assert.deepEqual(mergeFormalProgress(previous, stale), previous);
  assert.deepEqual(mergeFormalProgress(previous, null), previous);
});

test('accepts forward progress and advances the current execution unit', () => {
  const previous: FormalProgress = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 18, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: 'M1 遮挡实验',
    currentUnits: ['mtl_global/17', 'mtl_global/29'],
    currentPair: 10,
    maskPair: 10,
  };
  const next: FormalProgress = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 20, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: 'M1 遮挡实验',
    currentUnits: ['mtl_global/43', 'no_statement_head/17'],
    currentPair: 11,
    maskPair: 11,
  };

  assert.deepEqual(mergeFormalProgress(previous, next), next);
});

test('uses the active pair and scoped units instead of the next history action', () => {
  const progress = deriveFormalProgress([
    { stage: 'M1_mask', status: 'TWELFTH_PAIR_IN_PROGRESS', completed_m1_mask_cells: 22 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Blocking condition | none; M1 mask pair 12 is in progress |',
    '| Primary result | partial only; 22/30 M1 mask cells complete and validated |',
    '| Frontend current phase | M1_mask |',
    '| Frontend current units | `M1/hires_aux/29`, `M1/hires_aux/43` |',
    '| 26 | EXECUTION_IN_PROGRESS | EXECUTION_IN_PROGRESS | pair 12 | running | decide whether to advance pair 13 |',
  ].join('\n'));

  assert.equal(progress?.maskPair, 12);
  assert.equal(progress?.currentPair, 12);
  assert.deepEqual(progress?.currentUnits, ['hires_aux/29', 'hires_aux/43']);
});

test('derives external prediction and masking progress from formal artifacts', () => {
  const progress = deriveFormalProgress([
    { stage: 'M1_mask', completed_m1_mask_cells: 30 },
    { stage: 'M2_external_predict', completed_m2_prediction_cells: 8 },
    { stage: 'M2_external_mask', completed_m2_mask_cells: 0 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Blocking condition | none; M2 external prediction pair 5 is in progress |',
    '| Primary result | partial only; 30/30 M1 mask cells and 8/15 M2 prediction cells complete and validated; 0/12 M2 mask cells complete |',
    '| Frontend current phase | M2_external_predict |',
    '| Frontend current units | `M2/mtl_global/43`, `M2/direct_combo/17` |',
  ].join('\n'));

  assert.deepEqual(progress?.externalPrediction, { completed: 8, total: 15 });
  assert.deepEqual(progress?.externalMasking, { completed: 0, total: 12 });
  assert.equal(progress?.currentPair, 5);
  assert.equal(progress?.maskPair, null);
  assert.deepEqual(progress?.currentUnits, ['mtl_global/43', 'direct_combo/17']);
});

test('upgrades a persisted snapshot written by the older frontend schema', () => {
  const legacy = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 16, total: 30 },
  } as FormalProgress;
  const current: FormalProgress = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 18, total: 30 },
    externalPrediction: null,
    externalMasking: null,
    currentLabel: 'M1 遮挡实验',
    currentUnits: ['mtl_global/17', 'mtl_global/29'],
    currentPair: 10,
    maskPair: 10,
  };

  assert.deepEqual(mergeFormalProgress(legacy, current), current);
});

test('completion artifacts clear the last active pair while preserving verified counts', () => {
  const previous: FormalProgress = {
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 30, total: 30 },
    externalPrediction: { completed: 15, total: 15 },
    externalMasking: { completed: 12, total: 12 },
    currentLabel: 'M2 外部遮挡',
    currentUnits: ['mtl_global/43', 'hires_aux/17'],
    currentPair: 6,
    maskPair: null,
  };
  const completed = deriveFormalProgress([
    { stage: 'M2_external_predict', completed_m2_prediction_cells: 15 },
    { stage: 'M2_external_mask', completed_m2_mask_cells: 12 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Current stage | EXECUTION_COMPLETE |',
    '| Primary result | complete formal execution: 36/36 training, 36/36 M1 prediction, 30/30 M1 mask, 15/15 M2 prediction, 12/12 M2 mask |',
    '| Frontend current phase | result_analysis |',
    '| Frontend current units | none; formal execution is complete |',
    '| Blocking condition | none; all formal commands passed |',
  ].join('\n'));

  assert.deepEqual(mergeFormalProgress(previous, completed), {
    mode: 'formal_v1',
    training: { completed: 36, total: 36 },
    prediction: { completed: 36, total: 36 },
    masking: { completed: 30, total: 30 },
    externalPrediction: { completed: 15, total: 15 },
    externalMasking: { completed: 12, total: 12 },
    currentLabel: 'result_analysis',
    currentUnits: [],
    currentPair: null,
    maskPair: null,
    snapshotComplete: true,
  });
});

test('complete formal counts clear a stale active pair after a transport disconnect', () => {
  const progress = deriveFormalProgress([
    { stage: 'validate_training', expected_cell_count: 36, pass_cell_count: 36 },
    { stage: 'M1_prediction', expected_total_cell_count: 36, pass_total_cell_count: 36 },
    { stage: 'M1_mask', completed_m1_mask_cells: 30 },
    { stage: 'M2_external_predict', completed_m2_prediction_cells: 15 },
    { stage: 'M2_external_mask', completed_m2_mask_cells: 12 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Current stage | EXECUTION_IN_PROGRESS |',
    '| Primary result | 30/30 M1 mask, 15/15 M2 prediction, 12/12 M2 mask |',
    '| Frontend current phase | formal training pair 2/3 |',
    '| Frontend current units | `ours/67`, `global_bypass/67` |',
    '| Blocking condition | stream disconnected after pair 2 |',
  ].join('\n'));

  assert.equal(progress?.snapshotComplete, true);
  assert.equal(progress?.currentLabel, null);
  assert.deepEqual(progress?.currentUnits, []);
  assert.equal(progress?.currentPair, null);
});

test('uses the active revision counts instead of completed formal v1 counts', () => {
  const progress = deriveFormalProgress([], [
    '| Field | Value |',
    '| --- | --- |',
    '| Current stage | EXECUTION_IN_PROGRESS |',
    '| Execution target | `formal_c2_v2/generated_project/` via `formal_c2_v2/command_plan.json` |',
    '| Primary result | formal v1 counts are immutable and new-run validated counts are training 4/6, prediction 0/6, paired evaluator 0/3 |',
    '| Frontend current phase | formal training pair 2/3 complete; pair 3 recovery check pending |',
    '| Frontend current units | none; next `M1-C2-CONFIRM-v2/ours/79`, `M1-C2-CONFIRM-v2/global_bypass/79` |',
    '| Blocking condition | none; seed-79 is pending read-only recovery checks |',
  ].join('\n'));

  assert.equal(progress?.mode, 'revision');
  assert.deepEqual(progress?.training, { completed: 4, total: 6 });
  assert.deepEqual(progress?.prediction, { completed: 0, total: 6 });
  assert.deepEqual(progress?.masking, { completed: 0, total: 3 });
  assert.deepEqual(progress?.currentUnits, []);
});

test('a human review breakpoint clears stale execution units', () => {
  const progress = deriveFormalProgress([
    { stage: 'M2_external_predict', completed_m2_prediction_cells: 15 },
    { stage: 'M2_external_mask', completed_m2_mask_cells: 12 },
  ], [
    '| Field | Value |',
    '| --- | --- |',
    '| Current stage | WAITING_FOR_METHOD_REVISION_APPROVAL |',
    '| Primary result | 30/30 M1 mask, 15/15 M2 prediction, 12/12 M2 mask |',
    '| Frontend current phase | method_revision_review |',
    '| Frontend current units | none; waiting for method revision approval |',
    '| Blocking condition | human decision required for Revision ID `REV-01` |',
  ].join('\n'));

  assert.equal(progress?.snapshotComplete, true);
  assert.deepEqual(progress?.currentUnits, []);
  assert.equal(progress?.currentPair, null);
});
