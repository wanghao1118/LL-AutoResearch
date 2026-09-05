export type Review = {
  revisionId: string;
  question: string;
  background: string;
  modification: string;
  rationale: string;
  validation: string;
  languageReady: boolean;
  atLimit: boolean;
};

export type RecordedDecision = {
  decision: string;
  revisionId: string;
};

export function latestRecordedDecision(events: Array<{ text?: string }>): RecordedDecision | null {
  for (const event of [...events].reverse()) {
    const match = event.text?.match(/已记录人工决定：([A-Z_]+)\s*·\s*([A-Z0-9._-]+)/);
    if (match) return { decision: match[1], revisionId: match[2] };
  }
  return null;
}

export function parseMethodRevisionDecision(markdown: string): RecordedDecision | null {
  const current = markdown.split(/^##\s+/m, 1)[0];
  const revisionId = current.match(/Revision ID[^\n]*`([^`\n]+)`/i)?.[1]?.trim();
  const decision = current.match(/(?:Current\s+)?Decision[^\n]*`([A-Z_]+)`/i)?.[1]?.trim();
  return revisionId && decision ? { revisionId, decision } : null;
}

function revisionIdFromProposal(proposal: string) {
  const codeValue = proposal.match(/Revision ID[^\n]*`([^`\n]+)`/i)?.[1]?.trim();
  if (codeValue) return codeValue;
  return proposal.match(/Revision ID[^A-Z0-9]+([A-Z][A-Z0-9._-]+)/i)?.[1]?.trim() || null;
}

function cleanReviewText(markdown: string) {
  return markdown
    .replace(/<!--[^]*?-->/g, ' ')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*>#]/g, '')
    .replace(/^\s*[-+]\s+/gm, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function proposalSection(proposal: string, heading: RegExp) {
  const lines = proposal.split('\n');
  const start = lines.findIndex((line) => {
    const match = line.match(/^(#{2,4})\s+(.+?)\s*$/);
    return Boolean(match && heading.test(cleanReviewText(match[2])));
  });
  if (start < 0) return '';
  const depth = lines[start].match(/^(#+)/)?.[1].length || 2;
  const body: string[] = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    const nextHeading = lines[index].match(/^(#+)\s+/);
    if (nextHeading && nextHeading[1].length <= depth) break;
    body.push(lines[index]);
  }
  return cleanReviewText(body.join('\n'));
}

function containsChinese(value: string) {
  return /[\u3400-\u9fff]/.test(value);
}

export function parseMethodRevisionProposal(proposal: string, recovery: string): Review | null {
  const revisionId = revisionIdFromProposal(proposal);
  if (!revisionId) return null;
  const limit = Number(recovery.match(/method_revision_limit\s*[:：|]\s*(\d+)/i)?.[1] || 2);
  const approved = Number(recovery.match(/approved_method_revisions\s*[:：|]\s*(\d+)/i)?.[1] || 0);
  const background = proposalSection(proposal, /^(审核背景|背景)(?:（中文）)?$/i);
  const modification = proposalSection(proposal, /^(具体修改方法|修改方法|修改方案)(?:（中文）)?$/i);
  const rationale = proposalSection(proposal, /^(设计思路|修改思路|为什么这样改)(?:（中文）)?$/i);
  const validation = proposalSection(proposal, /^(实验验证|验证、成本与回退|验证与回退)(?:（中文）)?$/i);
  const languageReady = [background, modification, rationale, validation].every(containsChinese);

  return {
    revisionId,
    question: languageReady
      ? approved >= limit
        ? '是否批准这次例外方法修改？选择 No 将废弃当前 Idea。'
        : '是否批准 Codex 提出的这项方法修改？'
      : '当前提案缺少完整的中文审核说明，暂不能批准。',
    background: background || 'Codex 尚未提供中文背景说明。',
    modification: modification || 'Codex 尚未提供中文修改方法。',
    rationale: rationale || 'Codex 尚未提供中文设计思路。',
    validation: validation || 'Codex 尚未提供中文实验验证与回退方案。',
    languageReady,
    atLimit: approved >= limit,
  };
}
