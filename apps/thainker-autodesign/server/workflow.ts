export function needsAuditReviewPreparation(
  stage: string,
  status: string,
  reviewPreparationAttempted: boolean,
) {
  return stage === 'INTEGRITY_AUDIT_FAIL'
    && status === 'failed'
    && !reviewPreparationAttempted;
}
