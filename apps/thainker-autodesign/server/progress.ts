export type ProgressCount = {
  completed: number;
  total: number;
};

export type FormalProgress = {
  mode?: 'formal_v1' | 'revision';
  training: ProgressCount | null;
  prediction: ProgressCount | null;
  masking: ProgressCount | null;
  externalPrediction: ProgressCount | null;
  externalMasking: ProgressCount | null;
  currentLabel: string | null;
  currentUnits: string[];
  currentPair: number | null;
  maskPair: number | null;
  snapshotComplete?: boolean;
};

export type ExecutionProgressEvent = {
  stage?: string;
  status?: string;
  expected_cell_count?: number;
  observed_cell_count?: number;
  pass_cell_count?: number;
  expected_total_cell_count?: number;
  observed_total_cell_count?: number;
  pass_total_cell_count?: number;
  completed_m1_mask_cells?: number;
  completed_m2_prediction_cells?: number;
  completed_m2_mask_cells?: number;
};

function stateValue(markdown: string, field: string) {
  const match = markdown.match(new RegExp(`\\|\\s*${field}\\s*\\|\\s*([^|]+)\\|`, 'i'));
  return match?.[1]?.trim() || '';
}

function latestEvent(events: ExecutionProgressEvent[], stage: string) {
  return [...events].reverse().find((event) => event.stage === stage);
}

function progressCount(completed: unknown, total: unknown): ProgressCount | null {
  const parsedCompleted = Number(completed);
  const parsedTotal = Number(total);
  if (!Number.isFinite(parsedCompleted) || !Number.isFinite(parsedTotal) || parsedTotal <= 0) return null;
  return {
    completed: Math.max(0, Math.min(parsedCompleted, parsedTotal)),
    total: parsedTotal,
  };
}

function currentUnitsFromState(state: string) {
  const explicit = stateValue(state, 'Frontend current units');
  if (/^(?:none|无)(?:\b|[；;，,])/i.test(explicit)) return [];
  const latestHistoryAction = state
    .split('\n')
    .filter((line) => /^\|\s*\d+\s*\|/.test(line))
    .at(-1)
    ?.split('|')
    .at(-2)
    ?.trim() || '';
  const source = explicit || latestHistoryAction;
  const rawUnits = Array.from(source.matchAll(/`([^`]*\/\d+)`/g), (match) => match[1]);
  const normalized: string[] = [];
  let family = '';
  for (const rawUnit of rawUnits) {
    const scopedUnit = rawUnit.match(/^M[12]\/([a-z][a-z0-9_]*)\/(\d+)$/i);
    if (scopedUnit) {
      family = scopedUnit[1];
      normalized.push(`${scopedUnit[1]}/${scopedUnit[2]}`);
    } else if (/^[^/]+\/[a-z][a-z0-9_]*\/\d+$/i.test(rawUnit)) {
      const [, variant, seed] = rawUnit.match(/^[^/]+\/([a-z][a-z0-9_]*)\/(\d+)$/i) || [];
      family = variant;
      normalized.push(`${variant}/${seed}`);
    } else if (/^[a-z][a-z0-9_]*\/\d+$/i.test(rawUnit)) {
      family = rawUnit.split('/')[0];
      normalized.push(rawUnit);
    } else if (/^\/\d+$/.test(rawUnit) && family) {
      normalized.push(`${family}${rawUnit}`);
    }
  }
  return [...new Set(normalized)];
}

export function deriveFormalProgress(events: ExecutionProgressEvent[], state: string): FormalProgress | null {
  const primaryResult = stateValue(state, 'Primary result');
  const revisionTraining = primaryResult.match(/\btraining\s+(\d+)\s*\/\s*(\d+)/i);
  const revisionPrediction = primaryResult.match(/\bprediction\s+(\d+)\s*\/\s*(\d+)/i);
  const revisionEvaluation = primaryResult.match(/\bpaired evaluator\s+(\d+)\s*\/\s*(\d+)/i);
  if (revisionTraining && revisionPrediction && revisionEvaluation) {
    const training = progressCount(revisionTraining[1], revisionTraining[2]);
    const prediction = progressCount(revisionPrediction[1], revisionPrediction[2]);
    const evaluation = progressCount(revisionEvaluation[1], revisionEvaluation[2]);
    const snapshotComplete = [training, prediction, evaluation]
      .every((progress) => Boolean(progress?.total && progress.completed >= progress.total));
    const blockingCondition = stateValue(state, 'Blocking condition');
    const pairMatches = Array.from(`${blockingCondition}\n${stateValue(state, 'Frontend current phase')}`.matchAll(/pair\s*(\d+)/gi));
    return {
      mode: 'revision',
      training,
      prediction,
      masking: evaluation,
      externalPrediction: null,
      externalMasking: null,
      currentLabel: snapshotComplete ? null : stateValue(state, 'Frontend current phase') || null,
      currentUnits: snapshotComplete ? [] : currentUnitsFromState(state),
      currentPair: snapshotComplete ? null : Number(pairMatches.at(-1)?.[1] || 0) || null,
      maskPair: null,
      ...(snapshotComplete ? { snapshotComplete: true } : {}),
    };
  }

  const trainingGate = latestEvent(events, 'validate_training');
  const predictionGate = latestEvent(events, 'M1_prediction');
  const training = progressCount(
    trainingGate?.pass_cell_count ?? trainingGate?.observed_cell_count,
    trainingGate?.expected_cell_count,
  );
  const prediction = progressCount(
    predictionGate?.pass_total_cell_count ?? predictionGate?.observed_total_cell_count,
    predictionGate?.expected_total_cell_count,
  );

  const recordMaskCompleted = Math.max(
    0,
    ...events.map((event) => Number(event.completed_m1_mask_cells || 0)),
  );
  const stateCounts = Array.from(
    state.matchAll(/(\d+)\s*\/\s*(\d+)\s*M1\s*(?:mask|遮挡)/gi),
    (match) => ({ completed: Number(match[1]), total: Number(match[2]) }),
  ).sort((left, right) => right.completed - left.completed);
  const masking = stateCounts[0]
    ? progressCount(Math.max(recordMaskCompleted, stateCounts[0].completed), stateCounts[0].total)
    : null;

  const recordExternalPredictionCompleted = Math.max(
    0,
    ...events.map((event) => Number(event.completed_m2_prediction_cells || 0)),
  );
  const externalPredictionState = state.match(/(\d+)\s*\/\s*(\d+)\s*M2\s*(?:external\s*)?prediction/i);
  const externalPrediction = externalPredictionState
    ? progressCount(
      Math.max(recordExternalPredictionCompleted, Number(externalPredictionState[1])),
      Number(externalPredictionState[2]),
    )
    : null;

  const recordExternalMaskingCompleted = Math.max(
    0,
    ...events.map((event) => Number(event.completed_m2_mask_cells || 0)),
  );
  const externalMaskingState = state.match(/(\d+)\s*\/\s*(\d+)\s*M2\s*(?:external\s*)?mask/i);
  const externalMasking = externalMaskingState
    ? progressCount(
      Math.max(recordExternalMaskingCompleted, Number(externalMaskingState[1])),
      Number(externalMaskingState[2]),
    )
    : null;

  if (!training && !prediction && !masking && !externalPrediction && !externalMasking) return null;

  const artifactStage = stateValue(state, 'Current stage');
  const stageSnapshotComplete = [
    'WAITING_FOR_METHOD_REVISION_APPROVAL',
    'DESIGN_REVISION_IN_PROGRESS',
    'EXECUTION_PAUSED_BY_USER',
    'EXECUTION_COMPLETE',
    'RESULT_DIAGNOSIS_READY',
    'INTEGRITY_AUDIT_PASS',
    'COMPLETE',
  ].includes(artifactStage);
  const allFormalUnitsComplete = [training, prediction, masking, externalPrediction, externalMasking]
    .every((progress) => Boolean(progress?.total && progress.completed >= progress.total));
  const snapshotComplete = stageSnapshotComplete || allFormalUnitsComplete;
  const activePair = snapshotComplete
    ? undefined
    : stateValue(state, 'Blocking condition').match(/pair\s*(\d+)/i)?.[1];
  const pairMatches = Array.from(state.matchAll(/(?:pair\s*|第\s*)(\d+)(?:\s*对)?/gi));
  const currentPair = snapshotComplete ? null : Number(activePair || pairMatches.at(-1)?.[1] || 0) || null;
  const explicitLabel = stateValue(state, 'Frontend current phase');
  const currentLabel = stageSnapshotComplete
    ? explicitLabel || null
    : allFormalUnitsComplete
      ? null
      : explicitLabel
        || (externalMasking && externalMasking.completed < externalMasking.total ? 'M2_external_mask' : null)
        || (externalPrediction && externalPrediction.completed < externalPrediction.total ? 'M2_external_predict' : null)
        || (masking && masking.completed < masking.total ? 'M1 遮挡实验' : null)
        || (prediction && prediction.completed < prediction.total ? 'M1 正常预测' : null)
        || (training && training.completed < training.total ? '正式训练' : null);
  const maskPair = !snapshotComplete && /M1(?:_|\s)*(?:mask|遮挡)/i.test(currentLabel || '') ? currentPair : null;

  return {
    mode: 'formal_v1',
    training,
    prediction,
    masking,
    externalPrediction,
    externalMasking,
    currentLabel,
    currentUnits: snapshotComplete ? [] : currentUnitsFromState(state),
    currentPair,
    maskPair,
    ...(snapshotComplete ? { snapshotComplete: true } : {}),
  };
}

function mergeCount(previous: ProgressCount | null, next: ProgressCount | null) {
  if (!previous) return next;
  if (!next || next.completed < previous.completed) return previous;
  return next;
}

export function mergeFormalProgress(previous: FormalProgress | null | undefined, next: FormalProgress | null) {
  if (!previous) return next;
  if (!next) return previous;
  if (next.mode !== previous.mode && (next.mode === 'revision' || previous.mode === 'revision')) return next;
  const nextIsStale = [
    [previous.training, next.training],
    [previous.prediction, next.prediction],
    [previous.masking, next.masking],
    [previous.externalPrediction, next.externalPrediction],
    [previous.externalMasking, next.externalMasking],
  ].some(([before, after]) => before && after && after.completed < before.completed);
  if (nextIsStale) return previous;
  if (next.snapshotComplete) {
    return {
      ...((next.mode || previous.mode) ? { mode: next.mode || previous.mode } : {}),
      training: mergeCount(previous.training, next.training),
      prediction: mergeCount(previous.prediction, next.prediction),
      masking: mergeCount(previous.masking, next.masking),
      externalPrediction: mergeCount(previous.externalPrediction, next.externalPrediction),
      externalMasking: mergeCount(previous.externalMasking, next.externalMasking),
      currentLabel: next.currentLabel || null,
      currentUnits: [],
      currentPair: null,
      maskPair: null,
      snapshotComplete: true,
    };
  }
  return {
    ...((next.mode || previous.mode) ? { mode: next.mode || previous.mode } : {}),
    training: mergeCount(previous.training, next.training),
    prediction: mergeCount(previous.prediction, next.prediction),
    masking: mergeCount(previous.masking, next.masking),
    externalPrediction: mergeCount(previous.externalPrediction, next.externalPrediction),
    externalMasking: mergeCount(previous.externalMasking, next.externalMasking),
    currentLabel: next.currentLabel || previous.currentLabel || null,
    currentUnits: next.currentUnits.length ? next.currentUnits : previous.currentUnits || [],
    currentPair: next.currentPair || previous.currentPair || null,
    maskPair: Math.max(previous.maskPair || 0, next.maskPair || 0) || null,
  };
}
