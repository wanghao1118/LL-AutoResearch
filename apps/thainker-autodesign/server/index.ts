import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { mkdir, readFile, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { Codex, type ThreadEvent, type ThreadItem } from '@openai/codex-sdk';
import { parseRemoteGpuSnapshot, processIdsFromCsv, type RemoteGpuSnapshot } from './gpu-monitor';
import { deriveFormalProgress, mergeFormalProgress, type ExecutionProgressEvent, type FormalProgress } from './progress';
import { isRecoverableTransportDisconnect } from './recovery';
import { latestRecordedDecision, parseMethodRevisionDecision, parseMethodRevisionProposal, type RecordedDecision, type Review } from './review';
import { needsAuditReviewPreparation } from './workflow';

type TaskStatus = 'queued' | 'waiting_thread' | 'reconnecting' | 'running' | 'pausing' | 'paused' | 'ready' | 'waiting_review' | 'reported' | 'completed' | 'failed' | 'abandoned';

type TaskEvent = {
  id: string;
  at: string;
  kind: 'state' | 'message' | 'command' | 'file' | 'error';
  text: string;
};

type ResultAggregate = {
  family: 'main' | 'ablation' | 'case_study' | 'analysis';
  experimentId: string;
  variantId: string;
  benchmarkTaskId: string;
  metric: string;
  n: number;
  mean: number;
  sampleStd: number | null;
};

type TaskResults = {
  status: string;
  expectedCellCount: number;
  observedCellCount: number;
  automaticClaimVerdict: string;
  aggregates: ResultAggregate[];
};

type PlanFamily = 'main' | 'ablation' | 'case_study' | 'analysis';

type PlanExperiment = {
  id: string;
  family: PlanFamily;
  title: string;
  question: string;
  comparison: string;
  display: string;
  variants: string;
  claim: string;
  evidenceClass: string;
};

type TaskPlan = {
  ideaTitle: string;
  goal: string;
  contributions: string[];
  source: 'frontend_plan.json' | 'experiment_design.md' | 'idea.md';
  experiments: PlanExperiment[];
};

type ExperimentTask = {
  id: string;
  title: string;
  fileName: string;
  status: TaskStatus;
  stage: string;
  stageLabel: string;
  progress: number;
  threadId: string | null;
  sourceThreadId: string | null;
  threadRetryCount: number;
  transportRetryCount: number;
  controlAction: 'prepare_method_revision_review' | null;
  reviewPreparationAttempted: boolean;
  runDir: string;
  workingDirectory: string;
  imported: boolean;
  currentActivity: string;
  latestArtifact: string | null;
  review: Review | null;
  pendingDecision: { decision: string; revisionId: string } | null;
  decisionInFlight: RecordedDecision | null;
  results: TaskResults | null;
  formalProgress: FormalProgress | null;
  plan: TaskPlan | null;
  createdAt: string;
  updatedAt: string;
  events: TaskEvent[];
};

const port = Number(process.env.THAINKER_PORT || 4317);
const workspaceRoot = path.resolve(
  process.env.AUTODESIGN_WORKSPACE || path.join(process.cwd(), '..', '..'),
);
const outputRoot = path.join(workspaceRoot, 'assets', 'output');
const serviceRoot = path.join(outputRoot, 'thainker-autodesign');
const statePath = path.join(serviceRoot, 'tasks.json');
const maxConcurrentTasks = Math.max(1, Number(process.env.AUTODESIGN_TASK_CONCURRENCY || 1));
const codex = new Codex();
const codexModel = 'gpt-5.6-sol';
const codexReasoningEffort = 'xhigh';
const remoteGpuSshTarget = process.env.AUTODESIGN_GPU_SSH_TARGET || 'root@connect.westd.seetacloud.com';
const remoteGpuSshPort = Number(process.env.AUTODESIGN_GPU_SSH_PORT || 45017);
const remoteGpuHost = `${remoteGpuSshTarget.replace(/^.*@/, '')}:${remoteGpuSshPort}`;
const codexThreadOptions = {
  model: codexModel,
  modelReasoningEffort: codexReasoningEffort,
  sandboxMode: 'danger-full-access',
  approvalPolicy: 'never',
  networkAccessEnabled: true,
} as const;
const sseClients = new Set<ServerResponse>();
const pauseMarkerName = 'AUTODESIGN_PAUSE_REQUESTED';

let tasks: ExperimentTask[] = [];
let activeTasks = 0;
let remoteGpuSnapshot: RemoteGpuSnapshot = {
  status: 'loading',
  host: remoteGpuHost,
  checkedAt: null,
  lastSuccessfulAt: null,
  gpus: [],
  message: '正在读取远端 GPU',
};
let remoteGpuRefreshInFlight = false;
const pauseRequests = new Set<string>();
const threadRetryTimers = new Map<string, ReturnType<typeof setTimeout>>();
const transportRetryTimers = new Map<string, ReturnType<typeof setTimeout>>();
const artifactSyncs = new Set<string>();

class PauseRequested extends Error {}

function plainMarkdown(value: string) {
  return value
    .replace(/<!--[^]*?-->/g, ' ')
    .replace(/\\noindent\s*/g, '')
    .replace(/\\textbf\{([^}]*)\}/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_>#]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function markdownSection(markdown: string, heading: RegExp) {
  const lines = markdown.split('\n');
  const start = lines.findIndex((line) => /^##\s+/.test(line) && heading.test(line.replace(/^##\s+/, '').trim()));
  if (start < 0) return '';
  const body: string[] = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    if (/^##\s+/.test(lines[index])) break;
    body.push(lines[index]);
  }
  return body.join('\n').trim();
}

function firstProseParagraph(markdown: string) {
  return markdown
    .split(/\n\s*\n/)
    .map(plainMarkdown)
    .find((paragraph) => paragraph && !paragraph.startsWith('|') && !/^[-\d]+[.)\s]/.test(paragraph)) || '';
}

function ideaTitle(markdown: string) {
  const heading = markdown.split('\n').find((line) => /^#\s+/.test(line.trim()));
  return plainMarkdown(heading?.replace(/^#\s+/, '') || '当前实验 Idea');
}

function ideaGoal(markdown: string) {
  const explicit = markdownSection(markdown, /^(一句话目标|研究目标|总体目标|objective|research goal)$/i);
  if (explicit) return firstProseParagraph(explicit);
  const hypothesis = markdown.match(/\*\*(?:核心假设|研究假设)[:：]\*\*\s*([^\n]+)/i)?.[1];
  if (hypothesis) return plainMarkdown(hypothesis);
  const motivation = markdownSection(markdown, /^(motivation|研究动机|weakness|问题背景)$/i);
  return firstProseParagraph(motivation) || '等待实验设计补充总体目标。';
}

function ideaContributions(markdown: string) {
  const section = markdownSection(markdown, /^(contribution|contributions|核心贡献|贡献)$/i);
  if (!section) return [];
  return section
    .split(/\n\s*\n/)
    .map(plainMarkdown)
    .filter((paragraph) => paragraph && !paragraph.startsWith('|'));
}

function blockField(block: string, names: string[]) {
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const match = block.match(new RegExp(`^-\\s+(?:\\*\\*)?${escaped}(?:\\*\\*)?\\s*:\\s*(.+)$`, 'im'));
    if (match?.[1]) return plainMarkdown(match[1]);
  }
  return '';
}

function planFamily(id: string, block: string): PlanFamily {
  const explicit = block.match(/`family:\s*(main|ablation|case_study|analysis)`/i)?.[1] as PlanFamily | undefined;
  if (explicit) return explicit;
  if (id.startsWith('AB')) return 'ablation';
  if (id.startsWith('CS')) return 'case_study';
  if (id.startsWith('AN')) return 'analysis';
  return 'main';
}

function parseExperimentDesign(markdown: string): PlanExperiment[] {
  const experiments: PlanExperiment[] = [];
  const headings = [...markdown.matchAll(/^###\s+(M\d+|AB\d+|CS\d+|AN\d+)\s*[—–:-]\s*([^\n]+)$/gm)];
  for (let index = 0; index < headings.length; index += 1) {
    const match = headings[index];
    const id = match[1];
    const bodyStart = (match.index || 0) + match[0].length;
    let bodyEnd = headings[index + 1]?.index ?? markdown.length;
    const nextSectionOffset = markdown.slice(bodyStart, bodyEnd).search(/^##\s+/m);
    if (nextSectionOffset >= 0) bodyEnd = bodyStart + nextSectionOffset;
    const block = markdown.slice(bodyStart, bodyEnd);
    const intervention = blockField(block, ['Intervention', 'Intervention / removed component', 'Intervention / replaced component', '干预', '比较方式']);
    const reference = blockField(block, ['Matched reference', 'Reference', '匹配基线', '参照']);
    const primaryMetric = blockField(block, ['Primary metric', 'Primary metrics', '主要指标']);
    const metrics = blockField(block, ['Metrics', 'Split/metrics', '展示指标']);
    const displayFields = blockField(block, ['Display fields', 'Visible evidence', '展示内容']);
    const mappedClaims = blockField(block, ['Mapped claims', '对应贡献']) || plainMarkdown(block.match(/mapped\s+([^.;\n]+)/i)?.[1] || '');
    experiments.push({
      id,
      family: planFamily(id, block),
      title: plainMarkdown(match[2]),
      question: blockField(block, ['Research question', 'Question', 'Paper question', '研究问题']),
      comparison: [intervention, reference ? `参照：${reference}` : ''].filter(Boolean).join('；'),
      display: [primaryMetric, metrics, displayFields].filter(Boolean).join('；'),
      variants: blockField(block, ['Variants', 'Contexts/levels', 'Axis/levels', '变体']),
      claim: mappedClaims,
      evidenceClass: plainMarkdown(block.match(/`evidence_class:\s*([^`]+)`/i)?.[1] || ''),
    });
  }
  return experiments;
}

async function readTaskPlan(task: Pick<ExperimentTask, 'runDir'>): Promise<TaskPlan | null> {
  try {
    const summary = JSON.parse(await readFile(path.join(task.runDir, 'frontend_plan.json'), 'utf8')) as TaskPlan;
    if (summary.ideaTitle && Array.isArray(summary.experiments)) return { ...summary, source: 'frontend_plan.json' };
  } catch {
    // Fall back to the scientific Markdown artifacts below.
  }
  const idea = await readFile(path.join(task.runDir, 'idea.md'), 'utf8')
    .catch(() => readFile(path.join(task.runDir, 'input_brief.md'), 'utf8').catch(() => ''));
  const design = await readFile(path.join(task.runDir, 'experiment_design.md'), 'utf8').catch(() => '');
  if (!idea && !design) return null;
  return {
    ideaTitle: ideaTitle(idea || design),
    goal: ideaGoal(idea || design),
    contributions: ideaContributions(idea),
    source: design ? 'experiment_design.md' : 'idea.md',
    experiments: design ? parseExperimentDesign(design) : [],
  };
}

function pauseMarkerPath(task: ExperimentTask) {
  return path.join(task.runDir, pauseMarkerName);
}

async function writePauseMarker(task: ExperimentTask) {
  await writeFile(
    pauseMarkerPath(task),
    `task_id=${task.id}\nrequested_at=${new Date().toISOString()}\n`,
  );
}

async function clearPauseMarker(task: ExperimentTask) {
  await rm(pauseMarkerPath(task), { force: true });
}

const stageMeta: Record<string, { label: string; progress: number }> = {
  INPUT_READY: { label: 'Idea 解析', progress: 10 },
  EXPERIMENT_DESIGN_READY: { label: '实验设计', progress: 34 },
  WAITING_FOR_R0: { label: '等待 R0', progress: 42 },
  R0_PASSED: { label: 'R0 已通过', progress: 50 },
  R0_FAILED_RETURN_TO_DESIGN: { label: '返回实验设计', progress: 38 },
  WAITING_FOR_METHOD_REVISION_APPROVAL: { label: '等待人工审核', progress: 58 },
  DESIGN_REVISION_IN_PROGRESS: { label: '设计修订', progress: 59 },
  IMPLEMENTATION_READY: { label: '实现就绪', progress: 60 },
  EXECUTION_IN_PROGRESS: { label: '正式实验', progress: 74 },
  EXECUTION_PAUSED_BY_USER: { label: '用户暂停', progress: 74 },
  EXECUTION_COMPLETE: { label: '实验完成', progress: 84 },
  RESULT_DIAGNOSIS_READY: { label: '结果诊断', progress: 91 },
  INTEGRITY_AUDIT_PASS: { label: '完整性审计', progress: 97 },
  INTEGRITY_AUDIT_FAIL: { label: '审计未通过', progress: 97 },
  COMPLETE: { label: '全部完成', progress: 100 },
  IDEA_ABANDONED: { label: 'Idea 已废弃', progress: 100 },
};

async function loadState() {
  await mkdir(serviceRoot, { recursive: true });
  try {
    tasks = JSON.parse(await readFile(statePath, 'utf8')) as ExperimentTask[];
    tasks = tasks.map((task) => {
      const recoverTrustFailure = task.imported && isGitTrustCheckFailure(task.currentActivity);
      const recoverSafePause = task.status === 'pausing';
      const recoverWriterConflict = task.status === 'waiting_thread'
        || (task.status === 'failed' && isActiveWriterConflict(task.currentActivity));
      const recoverTransport = task.status === 'reconnecting'
        || (task.status === 'failed' && isRecoverableTransportDisconnect(task.currentActivity));
      const recoverDesignRevision = task.stage === 'DESIGN_REVISION_IN_PROGRESS'
        && ['failed', 'waiting_review', 'running'].includes(task.status);
      const recoverAuditReview = needsAuditReviewPreparation(
        task.stage,
        task.status,
        task.reviewPreparationAttempted || false,
      );
      if (recoverSafePause) pauseRequests.add(task.id);
      return {
        ...task,
        status: recoverTrustFailure
          ? 'paused'
          : recoverWriterConflict || recoverTransport || recoverSafePause || recoverDesignRevision || recoverAuditReview || task.status === 'running'
            ? 'queued'
            : task.status,
        currentActivity: recoverTrustFailure
          ? '恢复入口已修复；实验仍保持暂停，可以再次点击“继续实验”'
          : recoverWriterConflict
            ? '服务已恢复，正在重新接续 Codex 任务'
          : recoverTransport
            ? '服务已恢复，正在核对现有实验产物并从断开的 Codex 回合继续'
          : recoverSafePause
            ? '本地服务已恢复，正在自动完成上次未结束的安全暂停'
          : recoverDesignRevision
            ? '服务已恢复，正在从已记录的人工批准继续设计修订'
          : recoverAuditReview
            ? '审计未通过，正在生成新的中文方法修订提案；批准前不会启动实验'
          : task.status === 'running' ? '服务已重新启动，任务等待恢复' : task.currentActivity,
        sourceThreadId: task.sourceThreadId || (task.imported ? task.threadId : null),
        threadRetryCount: task.threadRetryCount || 0,
        transportRetryCount: task.transportRetryCount || 0,
        controlAction: recoverAuditReview
          ? 'prepare_method_revision_review'
          : task.controlAction || null,
        reviewPreparationAttempted: task.reviewPreparationAttempted || false,
        workingDirectory: task.workingDirectory || workspaceRoot,
        imported: task.imported || false,
        pendingDecision: task.pendingDecision || null,
        decisionInFlight: task.decisionInFlight
          || (task.stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL' ? latestRecordedDecision(task.events) : null),
        results: task.results || null,
        formalProgress: task.formalProgress || null,
        plan: task.plan || null,
      };
    });
    await Promise.all(tasks.map(async (task) => {
      const [plan, formalProgress, review, fileDecision] = await Promise.all([
        readTaskPlan(task),
        readFormalProgress(task),
        task.stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL' ? readReview(task) : null,
        readMethodRevisionDecision(task),
      ]);
      task.plan = plan || task.plan;
      task.formalProgress = mergeFormalProgress(task.formalProgress, formalProgress);
      if (task.stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL') {
        const decisionAccepted = Boolean(
          review && task.decisionInFlight?.revisionId === review.revisionId,
        );
        task.review = decisionAccepted ? null : review;
        if (decisionAccepted && task.status === 'waiting_review') {
          task.status = 'queued';
          task.currentActivity = '已收到人工决定，正在等待 Codex 落实该 Revision ID';
        }
      }
      if (task.stage === 'INTEGRITY_AUDIT_FAIL' && fileDecision?.decision === 'REJECT_METHOD_REVISION') {
        const closureText = '用户选择 No：采用保守报告并结束本轮';
        task.status = 'reported';
        task.review = null;
        task.pendingDecision = null;
        task.decisionInFlight = null;
        task.currentActivity = '已选择不修改方法；真实负结果与证据缺口已按保守报告保存，本轮结束';
        if (!task.events.some((event) => event.text === closureText)) {
          task.events.push({ id: randomUUID(), at: new Date().toISOString(), kind: 'state', text: closureText });
          task.updatedAt = new Date().toISOString();
        }
      }
    }));
  } catch {
    tasks = [];
  }
}

async function saveState() {
  await mkdir(serviceRoot, { recursive: true });
  await writeFile(statePath, JSON.stringify(tasks, null, 2));
}

function publicTask(task: ExperimentTask) {
  return {
    id: task.id,
    title: task.title,
    fileName: task.fileName,
    status: task.status,
    stage: task.stage,
    stageLabel: task.stageLabel,
    progress: task.progress,
    threadId: task.threadId,
    sourceThreadId: task.sourceThreadId,
    runDir: task.runDir,
    workingDirectory: task.workingDirectory,
    imported: task.imported,
    currentActivity: task.currentActivity,
    latestArtifact: task.latestArtifact,
    review: task.review,
    results: task.results,
    formalProgress: task.formalProgress,
    plan: task.plan,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
    events: task.events.filter((event) => event.kind !== 'command').slice(-120),
  };
}

function broadcast() {
  const payload = `event: tasks\ndata: ${JSON.stringify(tasks.map(publicTask))}\n\n`;
  for (const client of sseClients) client.write(payload);
}

function broadcastRemoteGpu() {
  const payload = `event: gpu\ndata: ${JSON.stringify(remoteGpuSnapshot)}\n\n`;
  for (const client of sseClients) client.write(payload);
}

function runRemoteReadOnlyOnce(command: string) {
  return new Promise<string>((resolve, reject) => {
    execFile('ssh', [
      '-o', 'StrictHostKeyChecking=yes',
      '-o', 'ConnectTimeout=15',
      '-p', String(remoteGpuSshPort),
      remoteGpuSshTarget,
      command,
    ], {
      encoding: 'utf8',
      timeout: 20_000,
      maxBuffer: 2 * 1024 * 1024,
    }, (error, stdout) => {
      if (error) reject(error);
      else resolve(String(stdout));
    });
  });
}

async function runRemoteReadOnly(command: string) {
  try {
    return await runRemoteReadOnlyOnce(command);
  } catch {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return runRemoteReadOnlyOnce(command);
  }
}

async function refreshRemoteGpu() {
  if (remoteGpuRefreshInFlight) return;
  remoteGpuRefreshInFlight = true;
  const checkedAt = new Date().toISOString();
  try {
    const gpuCsv = await runRemoteReadOnly('nvidia-smi --query-gpu=index,uuid,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits');
    const processCsv = await runRemoteReadOnly('nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader,nounits');
    const processIds = [...new Set(processIdsFromCsv(processCsv))];
    const psOutput = processIds.length
      ? await runRemoteReadOnly(`ps -p ${processIds.join(',')} -o pid=,etime=,args=`).catch(() => '')
      : '';
    remoteGpuSnapshot = parseRemoteGpuSnapshot(remoteGpuHost, checkedAt, gpuCsv, processCsv, psOutput);
  } catch {
    remoteGpuSnapshot = {
      ...remoteGpuSnapshot,
      status: remoteGpuSnapshot.gpus.length ? 'stale' : 'unavailable',
      checkedAt,
      message: remoteGpuSnapshot.gpus.length ? '远端暂时不可达，正在显示上次成功采样' : '暂时无法连接远端 GPU',
    };
  } finally {
    remoteGpuRefreshInFlight = false;
    broadcastRemoteGpu();
  }
}

async function updateTask(id: string, patch: Partial<ExperimentTask>, event?: Omit<TaskEvent, 'id' | 'at'>) {
  const task = tasks.find((item) => item.id === id);
  if (!task) return;
  Object.assign(task, patch, { updatedAt: new Date().toISOString() });
  if (event) {
    task.events.push({ id: randomUUID(), at: new Date().toISOString(), ...event });
    task.events = task.events.slice(-120);
  }
  await saveState();
  broadcast();
}

function taskTitle(markdown: string, fileName: string) {
  const heading = markdown.split('\n').find((line) => /^#\s+/.test(line.trim()));
  return heading?.replace(/^#\s+/, '').trim() || fileName.replace(/\.md$/i, '').replaceAll(/[-_]/g, ' ');
}

function stageFromState(markdown: string) {
  const match = markdown.match(/\|\s*Current stage\s*\|\s*([A-Z0-9_]+)\s*\|/);
  return match?.[1] || null;
}

function stateValue(markdown: string, field: string) {
  const match = markdown.match(new RegExp(`\\|\\s*${field}\\s*\\|\\s*([^|]+)\\|`, 'i'));
  return match?.[1]?.trim() || null;
}

function threadIdFromReference(reference: string) {
  return reference.trim().match(/^(?:codex:\/\/threads\/)?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i)?.[1] || null;
}

function threadOptions(task: ExperimentTask) {
  return {
    ...codexThreadOptions,
    workingDirectory: task.workingDirectory,
    skipGitRepoCheck: true,
  };
}

function isGitTrustCheckFailure(message: string) {
  return message.includes('Not inside a trusted directory') && message.includes('--skip-git-repo-check');
}

function isActiveWriterConflict(message: string) {
  return message.includes('thread-store conflict') && message.includes('already has an active writer');
}

async function readFormalProgress(task: ExperimentTask): Promise<FormalProgress | null> {
  let events: ExecutionProgressEvent[] = [];
  for (const candidate of [
    path.join(task.runDir, 'execution_record.json'),
    path.join(task.runDir, 'formal_v1', 'execution_record.json'),
  ]) {
    try {
      const record = JSON.parse(await readFile(candidate, 'utf8')) as { events?: ExecutionProgressEvent[] };
      if (record.events?.length) {
        events = record.events;
        break;
      }
    } catch {
      continue;
    }
  }

  const state = await readFile(path.join(task.runDir, 'AUTODESIGN_STATE.md'), 'utf8').catch(() => '');
  return deriveFormalProgress(events, state);
}

async function readTaskResults(task: ExperimentTask): Promise<TaskResults | null> {
  try {
    const summary = JSON.parse(await readFile(path.join(task.runDir, 'result_summary.json'), 'utf8')) as {
      status?: string;
      expected_cell_count?: number;
      observed_cell_count?: number;
      automatic_claim_verdict?: string;
      aggregates?: Array<{
        experiment_id: string;
        variant_id: string;
        benchmark_task_id: string;
        metric: string;
        n: number;
        mean: number;
        sample_std?: number | null;
      }>;
    };
    const schedule = JSON.parse(await readFile(path.join(task.runDir, 'experiment_schedule.json'), 'utf8').catch(() => '{"cells":[]}')) as {
      cells?: Array<{
        experiment_id: string;
        variant_id: string;
        benchmark_task_id: string;
        family?: ResultAggregate['family'];
      }>;
    };
    const families = new Map<string, ResultAggregate['family']>();
    for (const cell of schedule.cells || []) {
      families.set(`${cell.experiment_id}|${cell.variant_id}|${cell.benchmark_task_id}`, cell.family || 'main');
    }
    return {
      status: summary.status || 'INCOMPLETE',
      expectedCellCount: Number(summary.expected_cell_count || 0),
      observedCellCount: Number(summary.observed_cell_count || 0),
      automaticClaimVerdict: summary.automatic_claim_verdict || 'NOT_ASSIGNED',
      aggregates: (summary.aggregates || []).map((aggregate) => ({
        family: families.get(`${aggregate.experiment_id}|${aggregate.variant_id}|${aggregate.benchmark_task_id}`) || 'main',
        experimentId: aggregate.experiment_id,
        variantId: aggregate.variant_id,
        benchmarkTaskId: aggregate.benchmark_task_id,
        metric: aggregate.metric,
        n: aggregate.n,
        mean: aggregate.mean,
        sampleStd: aggregate.sample_std ?? null,
      })),
    };
  } catch {
    return null;
  }
}

async function syncArtifacts(task: ExperimentTask) {
  if (artifactSyncs.has(task.id)) return;
  artifactSyncs.add(task.id);
  try {
    const state = await readFile(path.join(task.runDir, 'AUTODESIGN_STATE.md'), 'utf8');
    const stage = stageFromState(state);
    if (!stage) return;
    const meta = stageMeta[stage] || { label: stage, progress: task.progress };
    const [results, plan, formalProgress, review, fileDecision] = await Promise.all([
      readTaskResults(task),
      readTaskPlan(task),
      readFormalProgress(task),
      stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL' ? readReview(task) : null,
      readMethodRevisionDecision(task),
    ]);
    const nextResults = results || task.results;
    const nextPlan = plan || task.plan;
    const nextFormalProgress = mergeFormalProgress(task.formalProgress, formalProgress);
    const decisionAccepted = Boolean(
      stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
      && review
      && task.decisionInFlight?.revisionId === review.revisionId,
    );
    const nextReview = stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
      ? decisionAccepted ? null : review
      : null;
    const nextDecisionInFlight = stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
      ? task.decisionInFlight
      : null;
    const terminalConservativeReport = stage === 'INTEGRITY_AUDIT_FAIL'
      && fileDecision?.decision === 'REJECT_METHOD_REVISION';
    const nextStatus: TaskStatus = terminalConservativeReport
      ? 'reported'
      : stage === 'COMPLETE'
      ? 'completed'
      : stage === 'IDEA_ABANDONED'
        ? 'abandoned'
        : stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
          ? decisionAccepted ? task.status : 'waiting_review'
          : stage === 'DESIGN_REVISION_IN_PROGRESS'
            ? task.status === 'waiting_review' ? 'running' : task.status
          : stage === 'EXECUTION_PAUSED_BY_USER'
            ? 'paused'
            : ['EXECUTION_COMPLETE', 'RESULT_DIAGNOSIS_READY', 'INTEGRITY_AUDIT_PASS'].includes(stage)
              ? 'ready'
              : task.status;
    const stageActivity: Partial<Record<string, string>> = {
      EXECUTION_COMPLETE: '正式实验及注册分析已全部完成，等待继续进行结果诊断与完整性审计',
      RESULT_DIAGNOSIS_READY: '结果诊断已完成，等待继续进行完整性审计与流程收尾',
      INTEGRITY_AUDIT_PASS: '完整性审计已通过，等待完成最终报告与流程收尾',
      COMPLETE: '主实验、消融实验、结果诊断与审计均已完成',
      IDEA_ABANDONED: '当前 Idea 已废弃，已有实验记录保持不变',
      INTEGRITY_AUDIT_FAIL: terminalConservativeReport
        ? '已选择不修改方法；真实负结果与证据缺口已按保守报告保存，本轮结束'
        : '完整性审计未通过，等待处理科学断点',
    };
    const nextActivity = stageActivity[stage] || task.currentActivity;
    const nextArtifact = stage === 'EXECUTION_COMPLETE'
      ? 'formal_v1/assets/output/formal_result.json'
      : stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
        ? 'method_revision_proposal.md'
        : task.latestArtifact;
    const changed = stage !== task.stage
      || meta.label !== task.stageLabel
      || meta.progress !== task.progress
      || nextStatus !== task.status
      || nextActivity !== task.currentActivity
      || nextArtifact !== task.latestArtifact
      || JSON.stringify(nextReview) !== JSON.stringify(task.review)
      || JSON.stringify(nextDecisionInFlight) !== JSON.stringify(task.decisionInFlight)
      || JSON.stringify(nextResults) !== JSON.stringify(task.results)
      || JSON.stringify(nextPlan) !== JSON.stringify(task.plan)
      || JSON.stringify(nextFormalProgress) !== JSON.stringify(task.formalProgress);
    if (!changed) return;
    await updateTask(task.id, {
      stage,
      stageLabel: meta.label,
      progress: meta.progress,
      status: nextStatus,
      currentActivity: nextActivity,
      latestArtifact: nextArtifact,
      review: nextReview,
      decisionInFlight: nextDecisionInFlight,
      results: nextResults,
      plan: nextPlan,
      formalProgress: nextFormalProgress,
    });
  } catch {
    return;
  } finally {
    artifactSyncs.delete(task.id);
  }
}

async function readReview(task: ExperimentTask): Promise<Review | null> {
  try {
    const proposal = await readFile(path.join(task.runDir, 'method_revision_proposal.md'), 'utf8');
    const recovery = await readFile(path.join(task.runDir, 'breakpoint_recovery.md'), 'utf8').catch(() => '');
    return parseMethodRevisionProposal(proposal, recovery);
  } catch {
    return null;
  }
}

async function readMethodRevisionDecision(task: ExperimentTask): Promise<RecordedDecision | null> {
  try {
    return parseMethodRevisionDecision(
      await readFile(path.join(task.runDir, 'method_revision_decision.md'), 'utf8'),
    );
  } catch {
    return null;
  }
}

function describeItem(item: ThreadItem) {
  if (item.type === 'agent_message') {
    if (item.text.startsWith('Skill descriptions were shortened')) return null;
    return { kind: 'message' as const, text: item.text };
  }
  if (item.type === 'command_execution') return null;
  if (item.type === 'file_change') return { kind: 'file' as const, text: item.changes.map((change) => path.basename(change.path)).join('、') };
  if (item.type === 'error') return { kind: 'error' as const, text: item.message };
  return null;
}

async function consumeCodexEvents(
  task: ExperimentTask,
  events: AsyncGenerator<ThreadEvent>,
  honorPauseRequest = true,
) {
  for await (const event of events) {
    if (event.type === 'thread.started') {
      const continuingFromSource = Boolean(task.sourceThreadId && event.thread_id !== task.sourceThreadId);
      await updateTask(task.id, {
        threadId: event.thread_id,
        threadRetryCount: 0,
      }, continuingFromSource ? {
        kind: 'state',
        text: `已创建独立执行任务 ${event.thread_id}，从源任务产物继续`,
      } : undefined);
      continue;
    }
    if (event.type === 'item.completed' || event.type === 'item.updated') {
      const activity = describeItem(event.item);
      if (activity) {
        await updateTask(task.id, {
          currentActivity: activity.text,
          latestArtifact: activity.kind === 'file' ? activity.text : task.latestArtifact,
          transportRetryCount: activity.kind !== 'error' && event.type === 'item.completed'
            ? 0
            : task.transportRetryCount,
        }, activity);
      }
      await syncArtifacts(task);
      if (event.type === 'item.completed' && honorPauseRequest && pauseRequests.has(task.id)) {
        throw new PauseRequested();
      }
      continue;
    }
    if (event.type === 'turn.failed' || event.type === 'error') {
      const message = event.type === 'turn.failed' ? event.error.message : event.message;
      throw new Error(message);
    }
  }
}

function pauseControlPrompt(task: ExperimentTask) {
  return [
    `本任务的网站暂停标记是：${pauseMarkerPath(task)}`,
    '在启动每一个新的实验执行单元前检查该文件。文件存在时，不得启动新训练、预测、消融、分析、聚合或收集单元。',
    '如果标记在一个单元运行期间出现，只允许该在途单元自然结束并完成结果校验，然后把执行状态记录为 EXECUTION_PAUSED_BY_USER 并结束当前 Codex 回合。',
    '不要删除暂停标记；只有前端“继续实验”接口会清除它。不要把暂停当成实验失败或科学方法修改。',
  ].join('\n');
}

function frontendPlanPrompt(task: ExperimentTask) {
  return [
    `实验设计完成或修订后，同步维护中文前端摘要：${path.join(task.runDir, 'frontend_plan.json')}`,
    '该文件只做忠实展示，不改变 experiment_design.md。结构为 ideaTitle、goal、contributions、source、experiments；experiments 每项包含 id、family、title、question、comparison、display、variants、claim、evidenceClass。',
    'family 只能是 main、ablation、case_study、analysis。所有自然语言字段使用中文；方法名、数据集名、指标名和实验 ID 保留原始技术标识。',
    '摘要必须覆盖真实实验卡，不能写固定占位数量，不能填模拟结果或预期获胜数值。',
  ].join('\n');
}

function frontendProgressContractPrompt(task: ExperimentTask) {
  return [
    '前端进度只能来自运行目录中的结构化实验产物，不能只写在 Codex 自然语言回复里。',
    '每次开始或完成一个阶段、实验单元、暂停收尾或人工断点时，先更新 AUTODESIGN_STATE.md 和对应 execution_record.json，再输出进展说明。',
    'AUTODESIGN_STATE.md 的 Current stage、Primary result、Blocking condition 和 History 最后一行必须反映同一个已验证快照；完成数量只在结果合同校验通过后增加，暂停、恢复或切换 thread 时不得丢失已验证计数。',
    '正式实验进行中，在 AUTODESIGN_STATE.md 表格额外维护 Frontend current phase 和 Frontend current units；units 使用反引号包裹的真实 experiment_id/seed，多单元用逗号分隔。',
    `前端会每 5 秒读取这些产物；运行目录固定为：${task.runDir}`,
  ].join('\n');
}

function frontendReviewContractPrompt(task: ExperimentTask) {
  return [
    `人工审核提案文件固定为：${path.join(task.runDir, 'method_revision_proposal.md')}`,
    '进入 WAITING_FOR_METHOD_REVISION_APPROVAL 前，必须在提案开头依次写出四个中文二级标题：## 审核背景、## 具体修改方法、## 设计思路、## 实验验证。',
    '四段正文必须使用清楚、可独立理解的中文；方法名、指标名、数据集名、命令字面量、Revision ID 和实验 ID 可以保留英文。',
    '审核背景要说明当前证据哪里不足以及为什么必须由人决定；具体修改方法要说清改什么、不改什么；设计思路要解释因果逻辑和避免事后选择的方式；实验验证要写明实验单元、判定标准、成本和失败回退。',
    '缺少任一中文段落时前端会阻止 Yes/No，不得用英文原文、文件链接或“详见提案”替代中文摘要。',
  ].join('\n');
}

async function finishTurn(task: ExperimentTask) {
  await syncArtifacts(task);
  const current = tasks.find((item) => item.id === task.id);
  if (!current) return;
  if (current.stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL') {
    const review = await readReview(current);
    const decisionAccepted = Boolean(
      review && current.decisionInFlight?.revisionId === review.revisionId,
    );
    if (decisionAccepted && current.decisionInFlight?.decision === 'REJECT_METHOD_REVISION') {
      await updateTask(current.id, {
        status: 'reported',
        review: null,
        controlAction: null,
        decisionInFlight: null,
        currentActivity: '已选择不修改方法；现有负结果与证据缺口按保守报告保留，本轮结束',
      }, { kind: 'state', text: '用户选择 No：采用保守报告并结束本轮' });
      return;
    }
    await updateTask(current.id, decisionAccepted ? {
      status: 'failed',
      review: null,
      controlAction: null,
      currentActivity: '人工决定已记录，但 Codex 回合结束时尚未把该决定写入实验状态；可重新恢复执行，但无需再次审批',
    } : {
      status: 'waiting_review',
      review,
      controlAction: null,
      currentActivity: '等待人工审核最小方法修改',
    }, decisionAccepted
      ? { kind: 'error', text: '已记录的人工决定尚未被 Codex 落实，未重新开放审核' }
      : { kind: 'state', text: '任务已暂停，等待 Yes 或 No' });
  } else if (current.stage === 'EXECUTION_PAUSED_BY_USER') {
    await updateTask(current.id, {
      status: 'paused',
      currentActivity: '实验已按用户要求暂停，等待点击“继续实验”',
    }, { kind: 'state', text: '实验保持暂停，未自动继续' });
  } else if (current.stage === 'COMPLETE') {
    await updateTask(current.id, {
      status: 'completed',
      progress: 100,
      currentActivity: '主实验、消融实验、结果诊断与审计均已完成',
    }, { kind: 'state', text: '任务完成' });
  } else if (current.stage === 'IDEA_ABANDONED') {
    await updateTask(current.id, {
      status: 'abandoned',
      progress: 100,
      currentActivity: '已按人工决定废弃当前 Idea，并保留已有证据',
    }, { kind: 'state', text: 'Idea 已废弃' });
  } else if (['EXECUTION_COMPLETE', 'RESULT_DIAGNOSIS_READY', 'INTEGRITY_AUDIT_PASS'].includes(current.stage)) {
    const currentActivity = current.stage === 'EXECUTION_COMPLETE'
      ? '正式实验及注册分析已全部完成，等待继续进行结果诊断与完整性审计'
      : current.stage === 'RESULT_DIAGNOSIS_READY'
        ? '结果诊断已完成，等待继续进行完整性审计与流程收尾'
        : '完整性审计已通过，等待完成最终报告与流程收尾';
    await updateTask(current.id, {
      status: 'ready',
      currentActivity,
    }, { kind: 'state', text: currentActivity });
  } else if (
    current.stage === 'INTEGRITY_AUDIT_FAIL'
    && current.decisionInFlight?.decision === 'REJECT_METHOD_REVISION'
  ) {
    await updateTask(current.id, {
      status: 'reported',
      review: null,
      controlAction: null,
      decisionInFlight: null,
      currentActivity: '已选择不修改方法；现有负结果与证据缺口按保守报告保留，本轮结束',
    }, { kind: 'state', text: '用户选择 No：采用保守报告并结束本轮' });
  } else if (current.stage === 'INTEGRITY_AUDIT_FAIL' && !current.reviewPreparationAttempted) {
    await updateTask(current.id, {
      status: 'queued',
      controlAction: 'prepare_method_revision_review',
      currentActivity: '审计未通过，正在准备新的中文方法修订提案；批准前不会启动实验',
    }, { kind: 'state', text: '审计失败已转入人工方法修订审核准备' });
  } else {
    await updateTask(current.id, {
      status: 'failed',
      currentActivity: `Codex 已结束，但流程停在 ${current.stageLabel}`,
    }, { kind: 'error', text: '任务未到达完整终态，请查看 Codex 输出和运行产物' });
  }
}

async function runInitialTurn(task: ExperimentTask) {
  const thread = codex.startThread(threadOptions(task));
  const prompt = [
    '使用 $run-autodesign 完整执行这个 Idea。',
    `本任务的独立运行目录是：${task.runDir}`,
    `输入文件是：${path.join(task.runDir, 'idea.md')}`,
    '只处理这一项 Idea，不读取其他任务的观测结果作为本任务证据。',
    '遵守当前工作区的 AGENTS.md 和 AutoDesign Skill：普通执行断点自动做边界修复；只有进入 WAITING_FOR_METHOD_REVISION_APPROVAL 时才停止并等待人工决定；R0 仍按预注册科学门处理。',
    pauseControlPrompt(task),
    frontendPlanPrompt(task),
    frontendProgressContractPrompt(task),
    frontendReviewContractPrompt(task),
    '完成设计、实现、主实验、消融实验、案例分析、结果诊断与完整性审计，或在真实资源/人工断点处保留全部产物后停止。',
  ].join('\n');
  const streamed = await thread.runStreamed(prompt);
  await consumeCodexEvents(task, streamed.events);
}

async function runDecisionTurn(task: ExperimentTask, decision: string, revisionId: string) {
  if (!task.threadId) throw new Error('该任务还没有可恢复的 Codex thread');
  const thread = codex.resumeThread(task.threadId, threadOptions(task));
  const prompt = [
    `用户决定：${decision}`,
    `Revision ID：${revisionId}`,
    '把这项字面决定写入 method_revision_decision.md，并严格按 $run-autodesign 从当前断点继续。',
    '如果决定是 REJECT_METHOD_REVISION，不得再自动寻找另一条方法；保留现有证据、完整性审计和保守报告，结束本轮执行授权。如果决定是 ABANDON_IDEA，则保留全部历史与可复用产物后终止。',
    pauseControlPrompt(task),
    frontendPlanPrompt(task),
    frontendProgressContractPrompt(task),
    frontendReviewContractPrompt(task),
  ].join('\n');
  const streamed = await thread.runStreamed(prompt);
  await consumeCodexEvents(task, streamed.events);
}

async function runResumeTurn(task: ExperimentTask) {
  if (!task.threadId) throw new Error('该任务还没有可恢复的 Codex thread');
  const thread = codex.resumeThread(task.threadId, threadOptions(task));
  const streamed = await thread.runStreamed([
    '用户已在 The ThAInker Autodesign 前端明确点击“继续实验”。继续当前 $run-autodesign 任务。',
    `独立运行目录：${task.runDir}`,
    '先读取 AUTODESIGN_STATE.md 和已有产物，从第一个未完成或被失效的阶段继续，不重跑已经有效的昂贵阶段。',
    '在恢复任何执行阶段前，先只读核对本地与远端的在途进程、execution_record.json 和目标产物。旧单元仍在运行时只监控；已自然结束时先补收并校验结果合同；只有确认未启动且没有有效产物时才允许启动。绝不重复运行同一实验单元。',
    '普通执行断点继续按边界修复规则处理；仅在 WAITING_FOR_METHOD_REVISION_APPROVAL 时返回人工审核。',
    pauseControlPrompt(task),
    frontendPlanPrompt(task),
    frontendProgressContractPrompt(task),
    frontendReviewContractPrompt(task),
  ].join('\n'));
  await consumeCodexEvents(task, streamed.events);
}

async function runAuditReviewPreparationTurn(task: ExperimentTask, startFresh = false) {
  if (!task.threadId && !startFresh) throw new Error('该任务还没有可恢复的 Codex thread');
  const thread = startFresh
    ? codex.startThread(threadOptions(task))
    : codex.resumeThread(task.threadId!, threadOptions(task));
  const streamed = await thread.runStreamed([
    '使用 $run-autodesign 处理当前完整性审计断点。本回合只准备人工审核，不执行、不修改已接受的方法，也不启动任何训练、预测、评估、聚合或收集。',
    `运行目录：${task.runDir}`,
    '用户已明确要求：不能把需要新方法决定的 INTEGRITY_AUDIT_FAIL 直接显示为不可操作失败；必须把下一项最小科学修改以中文 Yes/No 审核返回前端。这个要求只授权生成提案，不代表批准提案。',
    '先读取 AUTODESIGN_STATE.md、breakpoint_recovery.md、method_revision_request.md、旧 method_revision_proposal.md、method_revision_decision.md、result_route.md 和 integrity_audit.md。保留所有有效结果和保守诊断。',
    '当前 Request ID 是 MRR-C2-KZERO-02，已批准方法修订为 1/2。新提案的 Revision ID 固定为 REV-C2-KZERO-02，不得复用旧 REV-C2-MATCHED-COVERAGE-01。旧提案的回退条款仍是已观测证据；当前用户指令要求把是否覆盖该回退条款本身升级为新的人工决定。',
    '按 Level 2 断点恢复，由 autodesign-experiment-design 写一个最小方法修改提案。提案必须明确改什么、不改什么，如何处理 seed 53/79 的 nucleus_shape K=0，避免根据正式结果挑选有利规则，并列出新增单元、判定标准、成本和失败回退。不要提前选择或实施任何修改。',
    '提案要明确告诉用户：Yes 表示批准该 Revision 并继续实验；No 表示不修改方法、采用当前保守报告并结束本轮。',
    frontendReviewContractPrompt(task),
    '先完整写入新的 method_revision_proposal.md，再把 AUTODESIGN_STATE.md 更新到标准状态 WAITING_FOR_METHOD_REVISION_APPROVAL；Blocking condition 必须包含新 Revision ID，并保持当前训练 6/6、预测 6/6、配对评估 1/3 等已验证计数不变。',
    '完成后立即结束回合，等待用户在前端点击 Yes 或 No。',
  ].join('\n'));
  await consumeCodexEvents(task, streamed.events);
}

async function runImportedContinuationTurn(
  task: ExperimentTask,
  lockedThreadId: string,
  pendingDecision: ExperimentTask['pendingDecision'],
) {
  const sourceThreadId = task.sourceThreadId || lockedThreadId;
  const thread = codex.startThread(threadOptions(task));
  const decisionPrompt = pendingDecision ? [
    `用户决定：${pendingDecision.decision}`,
    `Revision ID：${pendingDecision.revisionId}`,
    '先把这项字面决定写入 method_revision_decision.md，再从对应方法断点继续。',
  ] : [
    '用户已在 The ThAInker Autodesign 前端明确点击“继续实验”。',
  ];
  const streamed = await thread.runStreamed([
    '使用 $run-autodesign 接续一个已有实验。',
    `源 Codex 任务：${sourceThreadId}`,
    `实验目录：${task.runDir}`,
    '源任务当前由桌面 Codex 持有，禁止尝试并发写入或恢复源 thread；本任务是独立的后续执行 thread。',
    ...decisionPrompt,
    '把实验目录中的 AUTODESIGN_STATE.md、experiment_design.md、command_plan.json、result_contract.json、execution_record.json 和已有结果作为唯一恢复依据。',
    '启动新执行单元前先核对已有执行记录及本地/远端在途进程；若旧单元仍在运行，只监控并接收其结果，不得重复启动。',
    '从第一个未完成或已失效的阶段继续，不重跑已经有效的训练、预测、主实验、消融或分析单元。',
    '普通执行断点继续按边界修复规则处理；仅在 WAITING_FOR_METHOD_REVISION_APPROVAL 时返回人工审核。',
    pauseControlPrompt(task),
    frontendPlanPrompt(task),
    frontendProgressContractPrompt(task),
    frontendReviewContractPrompt(task),
  ].join('\n'));
  await consumeCodexEvents(task, streamed.events);
}

async function runSafePauseTurn(task: ExperimentTask) {
  if (!task.threadId) throw new Error('该任务还没有可执行安全暂停的 Codex thread');
  pauseRequests.delete(task.id);
  await updateTask(task.id, {
    status: 'pausing',
    currentActivity: 'Codex 已停止后续调度，正在自动检查在途单元并完成安全收尾',
  }, { kind: 'state', text: '已进入自动安全收尾：只处理在途单元，不再启动新单元' });

  const thread = codex.resumeThread(task.threadId, threadOptions(task));
  const streamed = await thread.runStreamed([
    '这是 The ThAInker Autodesign 后端发出的安全暂停控制回合。它不改变科学设计，也不授权继续实验。',
    `暂停标记：${pauseMarkerPath(task)}`,
    `运行目录：${task.runDir}`,
    '立即读取 AUTODESIGN_STATE.md、command_plan.json、result_contract.json、execution_record.json 和当前运行进程。',
    '不得启动任何新的训练、预测、消融、分析、聚合或收集单元。若存在已经启动的单元，只等待它自然结束，收集并校验该单元的完整结果；不得杀死、重启或替换它。',
    '确认本任务不再有本地或远端在途计算后，把 execution_record.json 的状态写为 EXECUTION_PAUSED_BY_USER，并在 AUTODESIGN_STATE.md 记录已完成数量、最后有效单元和精确恢复入口。',
    frontendProgressContractPrompt(task),
    '完成这些动作后立即结束回合。后续恢复只能由用户在前端点击“继续实验”触发。',
  ].join('\n'));
  await consumeCodexEvents(task, streamed.events, false);
  await syncArtifacts(task);
  const current = tasks.find((item) => item.id === task.id);
  if (!current) return;
  const executionStatus = await readFile(path.join(task.runDir, 'execution_record.json'), 'utf8')
    .then((content) => (JSON.parse(content) as { status?: string }).status || '')
    .catch(() => '');
  const formalExecutionStatus = await readFile(path.join(task.runDir, 'formal_v1', 'execution_record.json'), 'utf8')
    .then((content) => (JSON.parse(content) as { status?: string }).status || '')
    .catch(() => '');
  const stateStage = await readFile(path.join(task.runDir, 'AUTODESIGN_STATE.md'), 'utf8')
    .then(stageFromState)
    .catch(() => null);
  const confirmedByArtifact = [executionStatus, formalExecutionStatus, stateStage].includes('EXECUTION_PAUSED_BY_USER');
  const stage = stateStage || current.stage;
  const meta = stageMeta[stage] || { label: current.stageLabel, progress: current.progress };
  await updateTask(task.id, {
    status: 'paused',
    stage,
    stageLabel: meta.label,
    progress: meta.progress,
    currentActivity: confirmedByArtifact
      ? '安全暂停已完成：在途单元已收尾并校验，Codex 已停止，等待点击“继续实验”'
      : 'Codex 安全收尾回合已结束，后续调度已锁定，等待点击“继续实验”',
  }, { kind: 'state', text: '安全暂停完成；后续实验不会自动继续' });
}

function cancelThreadRetry(taskId: string) {
  const timer = threadRetryTimers.get(taskId);
  if (timer) clearTimeout(timer);
  threadRetryTimers.delete(taskId);
}

function cancelTransportRetry(taskId: string) {
  const timer = transportRetryTimers.get(taskId);
  if (timer) clearTimeout(timer);
  transportRetryTimers.delete(taskId);
}

async function scheduleThreadRetry(task: ExperimentTask) {
  cancelThreadRetry(task.id);
  const attempt = (task.threadRetryCount || 0) + 1;
  const delaySeconds = Math.min(60, 5 * (2 ** Math.min(attempt - 1, 4)));
  await updateTask(task.id, {
    status: 'waiting_thread',
    threadRetryCount: attempt,
    currentActivity: `Codex 任务暂时被另一个执行入口占用；${delaySeconds} 秒后自动重试`,
  }, {
    kind: 'state',
    text: `检测到 Codex 写锁占用，等待 ${delaySeconds} 秒后自动重试`,
  });
  const timer = setTimeout(() => {
    threadRetryTimers.delete(task.id);
    void (async () => {
      const current = tasks.find((item) => item.id === task.id);
      if (!current || current.status !== 'waiting_thread') return;
      await updateTask(current.id, {
        status: 'queued',
        currentActivity: 'Codex 任务写锁重试已进入队列',
      }, { kind: 'state', text: '正在重试连接 Codex 任务' });
      void drainQueue();
    })();
  }, delaySeconds * 1000);
  threadRetryTimers.set(task.id, timer);
}

async function scheduleTransportRetry(task: ExperimentTask) {
  cancelTransportRetry(task.id);
  await syncArtifacts(task);
  const current = tasks.find((item) => item.id === task.id) || task;
  if (['paused', 'ready', 'waiting_review', 'completed', 'abandoned'].includes(current.status)) return;
  const attempt = (current.transportRetryCount || 0) + 1;
  const delaySeconds = Math.min(60, 5 * (2 ** Math.min(attempt - 1, 4)));
  await updateTask(task.id, {
    status: 'reconnecting',
    transportRetryCount: attempt,
    currentActivity: `Codex 连接中断；实验进程和已有产物不受影响，${delaySeconds} 秒后自动从断点恢复`,
  }, {
    kind: 'state',
    text: `检测到可恢复的连接中断；已保留当前证据并安排第 ${attempt} 次自动续接`,
  });
  const timer = setTimeout(() => {
    transportRetryTimers.delete(task.id);
    void (async () => {
      const retryTask = tasks.find((item) => item.id === task.id);
      if (!retryTask || retryTask.status !== 'reconnecting') return;
      await updateTask(retryTask.id, {
        status: 'queued',
        currentActivity: '正在核对现有产物与远端进程，确认安全恢复点后继续',
      }, { kind: 'state', text: 'Codex 自动续接已进入队列' });
      void drainQueue();
    })();
  }, delaySeconds * 1000);
  transportRetryTimers.set(task.id, timer);
}

async function executeTask(task: ExperimentTask) {
  activeTasks += 1;
  const pendingDecision = task.pendingDecision || task.decisionInFlight;
  const recoveringPause = pauseRequests.has(task.id);
  const preparingAuditReview = task.controlAction === 'prepare_method_revision_review';
  await updateTask(task.id, {
    status: recoveringPause ? 'pausing' : 'running',
    currentActivity: recoveringPause
      ? '本地服务正在恢复并完成安全暂停'
      : preparingAuditReview
        ? '正在把审计失败整理为新的中文方法修订提案；批准前不会启动实验'
      : pendingDecision
        ? 'Codex 正在按人工决定恢复任务'
        : task.threadId ? 'Codex 正在从已有产物恢复任务' : 'Codex 正在读取 idea.md',
    review: null,
    pendingDecision: null,
    decisionInFlight: pendingDecision || task.decisionInFlight,
    reviewPreparationAttempted: preparingAuditReview ? true : task.reviewPreparationAttempted,
  }, { kind: 'state', text: recoveringPause ? '继续处理未完成的安全暂停' : '任务开始执行' });
  try {
    if (recoveringPause) {
      await runSafePauseTurn(task);
    } else if (preparingAuditReview) {
      await runAuditReviewPreparationTurn(task);
    } else if (pendingDecision) {
      await runDecisionTurn(task, pendingDecision.decision, pendingDecision.revisionId);
    } else if (task.threadId) {
      await runResumeTurn(task);
    } else {
      await runInitialTurn(task);
    }
    if (pauseRequests.has(task.id)) throw new PauseRequested();
    if (recoveringPause) return;
    await finishTurn(task);
  } catch (error) {
    if (error instanceof PauseRequested) {
      try {
        await runSafePauseTurn(task);
      } catch (pauseError) {
        const message = pauseError instanceof Error ? pauseError.message : '自动安全暂停失败';
        if (isRecoverableTransportDisconnect(message)) {
          await scheduleTransportRetry(task);
          return;
        }
        await updateTask(task.id, {
          status: 'pausing',
          currentActivity: `安全暂停尚未确认：${message}`,
        }, { kind: 'error', text: `安全暂停尚未确认：${message}` });
      }
      return;
    }
    const message = error instanceof Error ? error.message : 'Codex 执行失败';
    if (isActiveWriterConflict(message) && task.imported && task.threadId && !recoveringPause) {
      const lockedThreadId = task.threadId;
      await updateTask(task.id, {
        status: 'running',
        sourceThreadId: task.sourceThreadId || lockedThreadId,
        currentActivity: '源 Codex 任务由桌面端持有，正在创建独立执行任务并从原目录接续',
      }, { kind: 'state', text: '源任务不可并发写入；切换为基于原实验产物的独立执行任务' });
      try {
        if (preparingAuditReview) {
          await runAuditReviewPreparationTurn(task, true);
        } else {
          await runImportedContinuationTurn(task, lockedThreadId, pendingDecision);
        }
        if (pauseRequests.has(task.id)) throw new PauseRequested();
        await finishTurn(task);
      } catch (continuationError) {
        if (continuationError instanceof PauseRequested) {
          try {
            await runSafePauseTurn(task);
          } catch (pauseError) {
            const pauseMessage = pauseError instanceof Error ? pauseError.message : '自动安全暂停失败';
            if (isRecoverableTransportDisconnect(pauseMessage)) {
              await scheduleTransportRetry(task);
              return;
            }
            await updateTask(task.id, {
              status: 'pausing',
              currentActivity: `安全暂停尚未确认：${pauseMessage}`,
            }, { kind: 'error', text: `安全暂停尚未确认：${pauseMessage}` });
          }
          return;
        }
        pauseRequests.delete(task.id);
        const continuationMessage = continuationError instanceof Error ? continuationError.message : '独立执行任务启动失败';
        if (isRecoverableTransportDisconnect(continuationMessage)) {
          await scheduleTransportRetry(task);
          return;
        }
        await updateTask(task.id, {
          status: 'failed',
          currentActivity: continuationMessage,
        }, { kind: 'error', text: continuationMessage });
      }
      return;
    }
    if (isActiveWriterConflict(message)) {
      pauseRequests.delete(task.id);
      await scheduleThreadRetry(task);
      return;
    }
    if (isRecoverableTransportDisconnect(message)) {
      pauseRequests.delete(task.id);
      await scheduleTransportRetry(task);
      return;
    }
    pauseRequests.delete(task.id);
    const recoverTrustFailure = task.imported && isGitTrustCheckFailure(message);
    await updateTask(task.id, {
      status: recoverTrustFailure ? 'paused' : 'failed',
      currentActivity: recoverTrustFailure
        ? 'Codex 尚未开始执行；实验保持暂停，可以再次点击“继续实验”'
        : message,
    }, { kind: 'error', text: message });
  } finally {
    activeTasks -= 1;
    void drainQueue();
  }
}

async function drainQueue() {
  while (activeTasks < maxConcurrentTasks) {
    const task = tasks.find((item) => item.status === 'queued');
    if (!task) return;
    task.status = 'running';
    void executeTask(task);
  }
}

async function parseBody(request: IncomingMessage) {
  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.from(chunk));
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}') as Record<string, unknown>;
}

function sendJson(response: ServerResponse, status: number, data: unknown) {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
  response.end(JSON.stringify(data));
}

function routeMatch(pathname: string, suffix: string) {
  const match = pathname.match(new RegExp(`^/api/tasks/([^/]+)/${suffix}$`));
  return match?.[1] || null;
}

async function handleRequest(request: IncomingMessage, response: ServerResponse) {
  const url = new URL(request.url || '/', `http://${request.headers.host || '127.0.0.1'}`);
  if (request.method === 'OPTIONS') {
    response.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    });
    response.end();
    return;
  }
  if (request.method === 'GET' && url.pathname === '/api/health') {
    sendJson(response, 200, {
      ok: true,
      workspaceRoot,
      maxConcurrentTasks,
      model: codexModel,
      reasoningEffort: codexReasoningEffort,
      capabilities: { pause: true, autoReconnect: true, eventHistory: true, milestoneProgress: true, artifactSnapshots: true, remoteGpuMonitor: true },
    });
    return;
  }
  if (request.method === 'GET' && url.pathname === '/api/gpu') {
    sendJson(response, 200, remoteGpuSnapshot);
    return;
  }
  if (request.method === 'GET' && url.pathname === '/api/tasks') {
    sendJson(response, 200, tasks.map(publicTask));
    return;
  }
  if (request.method === 'GET' && url.pathname === '/api/events') {
    response.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    response.write(`event: tasks\ndata: ${JSON.stringify(tasks.map(publicTask))}\n\n`);
    response.write(`event: gpu\ndata: ${JSON.stringify(remoteGpuSnapshot)}\n\n`);
    sseClients.add(response);
    request.on('close', () => sseClients.delete(response));
    return;
  }
  if (request.method === 'POST' && url.pathname === '/api/tasks') {
    const body = await parseBody(request);
    const fileName = String(body.fileName || 'idea.md');
    const ideaMarkdown = String(body.ideaMarkdown || '');
    const requestedWorkingDirectory = String(body.workingDirectory || workspaceRoot);
    if (!ideaMarkdown.trim()) {
      sendJson(response, 400, { error: 'idea.md 不能为空' });
      return;
    }
    if (!path.isAbsolute(requestedWorkingDirectory)) {
      sendJson(response, 400, { error: '实验项目目录必须是绝对路径' });
      return;
    }
    const workingDirectory = path.resolve(requestedWorkingDirectory);
    const workingDirectoryStat = await stat(workingDirectory).catch(() => null);
    if (!workingDirectoryStat?.isDirectory()) {
      sendJson(response, 400, { error: '实验项目目录不存在或不是文件夹' });
      return;
    }
    const id = randomUUID();
    const runName = `thainker_${new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 14)}_${id.slice(0, 6)}`;
    const runDir = path.join(workingDirectory, 'assets', 'output', runName);
    await mkdir(runDir, { recursive: true });
    await writeFile(path.join(runDir, 'idea.md'), ideaMarkdown);
    const now = new Date().toISOString();
    const task: ExperimentTask = {
      id,
      title: taskTitle(ideaMarkdown, fileName),
      fileName,
      status: 'queued',
      stage: 'INPUT_READY',
      stageLabel: '等待执行',
      progress: 0,
      threadId: null,
      sourceThreadId: null,
      threadRetryCount: 0,
      transportRetryCount: 0,
      controlAction: null,
      reviewPreparationAttempted: false,
      runDir,
      workingDirectory,
      imported: false,
      currentActivity: '已创建独立任务，等待 Codex',
      latestArtifact: 'idea.md',
      review: null,
      pendingDecision: null,
      decisionInFlight: null,
      results: null,
      formalProgress: null,
      plan: null,
      createdAt: now,
      updatedAt: now,
      events: [{ id: randomUUID(), at: now, kind: 'state', text: '任务已进入队列' }],
    };
    task.plan = await readTaskPlan(task);
    tasks.unshift(task);
    await saveState();
    broadcast();
    void drainQueue();
    sendJson(response, 201, publicTask(task));
    return;
  }
  if (request.method === 'POST' && url.pathname === '/api/tasks/import') {
    const body = await parseBody(request);
    const threadReference = String(body.threadReference || '');
    const threadId = threadIdFromReference(threadReference);
    const workingDirectory = path.resolve(String(body.workingDirectory || ''));
    if (!threadId) {
      sendJson(response, 400, { error: '请输入有效的 Codex 任务链接或 thread ID' });
      return;
    }
    if (!body.workingDirectory || !path.isAbsolute(String(body.workingDirectory))) {
      sendJson(response, 400, { error: '请输入实验所在的绝对路径' });
      return;
    }
    const existing = tasks.find((task) => task.threadId === threadId);
    if (existing) {
      sendJson(response, 409, { error: '这个 Codex 任务已经导入', task: publicTask(existing) });
      return;
    }
    let state: string;
    try {
      state = await readFile(path.join(workingDirectory, 'AUTODESIGN_STATE.md'), 'utf8');
    } catch {
      sendJson(response, 400, { error: '该目录中没有 AUTODESIGN_STATE.md，无法确定安全恢复点' });
      return;
    }
    const stage = stageFromState(state);
    if (!stage) {
      sendJson(response, 400, { error: 'AUTODESIGN_STATE.md 中没有 Current stage' });
      return;
    }
    const meta = stageMeta[stage] || { label: stage, progress: 0 };
    const runName = stateValue(state, 'Run') || path.basename(workingDirectory);
    const lastCompleted = stateValue(state, 'Last completed stage');
    const importedStatus: TaskStatus = stage === 'COMPLETE'
      ? 'completed'
      : stage === 'IDEA_ABANDONED'
        ? 'abandoned'
        : stage === 'WAITING_FOR_METHOD_REVISION_APPROVAL'
          ? 'waiting_review'
          : ['EXECUTION_COMPLETE', 'RESULT_DIAGNOSIS_READY', 'INTEGRITY_AUDIT_PASS'].includes(stage)
            ? 'ready'
            : 'paused';
    const now = new Date().toISOString();
    const task: ExperimentTask = {
      id: randomUUID(),
      title: String(body.title || '').trim() || `继续已有实验：${runName}`,
      fileName: '已有 Codex 任务',
      status: importedStatus,
      stage,
      stageLabel: meta.label,
      progress: meta.progress,
      threadId,
      sourceThreadId: threadId,
      threadRetryCount: 0,
      transportRetryCount: 0,
      controlAction: null,
      reviewPreparationAttempted: false,
      runDir: workingDirectory,
      workingDirectory,
      imported: true,
      currentActivity: lastCompleted
        ? `已导入原任务，最近完成 ${lastCompleted}；尚未继续执行`
        : '已导入原任务；尚未继续执行',
      latestArtifact: 'AUTODESIGN_STATE.md',
      review: null,
      pendingDecision: null,
      decisionInFlight: null,
      results: null,
      formalProgress: null,
      plan: null,
      createdAt: now,
      updatedAt: now,
      events: [{ id: randomUUID(), at: now, kind: 'state', text: '已导入已有 Codex 任务，未自动继续执行' }],
    };
    task.plan = await readTaskPlan(task);
    if (importedStatus === 'waiting_review') {
      task.review = await readReview(task);
      if (!task.review) {
        sendJson(response, 400, { error: '任务处于人工审核断点，但目录中缺少有效的 Revision ID 提案' });
        return;
      }
      task.currentActivity = '已导入原任务，等待对当前 Revision ID 选择 Yes 或 No';
    }
    tasks.unshift(task);
    await saveState();
    await syncArtifacts(task);
    broadcast();
    sendJson(response, 201, publicTask(task));
    return;
  }
  const resumeTaskId = routeMatch(url.pathname, 'resume');
  if (request.method === 'POST' && resumeTaskId) {
    const task = tasks.find((item) => item.id === resumeTaskId);
    if (!task || !['paused', 'ready'].includes(task.status) || !task.threadId) {
      sendJson(response, 409, { error: '该任务当前不能从暂停点继续' });
      return;
    }
    await clearPauseMarker(task);
    cancelThreadRetry(task.id);
    cancelTransportRetry(task.id);
    pauseRequests.delete(task.id);
    const wasReadyForDiagnosis = task.status === 'ready';
    task.status = 'queued';
    task.threadRetryCount = 0;
    task.transportRetryCount = 0;
    task.transportRetryCount = 0;
    task.currentActivity = wasReadyForDiagnosis
      ? '已确认继续，等待 Codex 进入结果诊断与完整性审计'
      : '已确认继续，等待 Codex 从原断点恢复';
    task.events.push({
      id: randomUUID(),
      at: new Date().toISOString(),
      kind: 'state',
      text: wasReadyForDiagnosis ? '用户已点击继续结果诊断' : '用户已点击继续实验',
    });
    await saveState();
    broadcast();
    void drainQueue();
    sendJson(response, 200, publicTask(task));
    return;
  }
  const pauseTaskId = routeMatch(url.pathname, 'pause');
  if (request.method === 'POST' && pauseTaskId) {
    const task = tasks.find((item) => item.id === pauseTaskId);
    if (!task || !['running', 'waiting_thread', 'reconnecting'].includes(task.status)) {
      sendJson(response, 409, { error: '该任务当前不在运行中' });
      return;
    }
    await writePauseMarker(task);
    if (task.status === 'waiting_thread' || task.status === 'reconnecting') {
      cancelThreadRetry(task.id);
      cancelTransportRetry(task.id);
      pauseRequests.delete(task.id);
      await updateTask(task.id, {
        status: 'paused',
        currentActivity: task.status === 'reconnecting'
          ? '已取消 Codex 自动重连；现有实验产物保持不变'
          : '已取消 Codex 写锁重试；实验保持暂停',
      }, { kind: 'state', text: '已取消自动续接，实验保持暂停' });
      sendJson(response, 200, publicTask(task));
      return;
    }
    pauseRequests.add(task.id);
    await updateTask(task.id, {
      status: 'pausing',
      currentActivity: '暂停标记已生效；后台将自动等待当前执行节点结束、校验并停止 Codex',
    }, { kind: 'state', text: '已请求自动安全暂停：禁止新单元，当前单元结束后由后台完成收尾' });
    sendJson(response, 200, publicTask(task));
    return;
  }
  const decisionTaskId = routeMatch(url.pathname, 'decision');
  if (request.method === 'POST' && decisionTaskId) {
    const task = tasks.find((item) => item.id === decisionTaskId);
    const body = await parseBody(request);
    const revisionId = String(body.revisionId || '');
    if (task?.decisionInFlight?.revisionId === revisionId) {
      sendJson(response, 200, publicTask(task));
      return;
    }
    if (!task || task.status !== 'waiting_review' || !task.review) {
      sendJson(response, 409, { error: '该任务当前不在人工审核断点' });
      return;
    }
    if (!task.review.languageReady) {
      sendJson(response, 409, { error: '当前提案缺少完整中文说明，已阻止批准或拒绝操作' });
      return;
    }
    const approved = body.approved === true;
    if (revisionId !== task.review.revisionId) {
      sendJson(response, 409, { error: 'Revision ID 与当前提案不一致' });
      return;
    }
    const decision = task.review.atLimit
      ? approved ? 'APPROVE_EXCEPTION_METHOD_REVISION' : 'ABANDON_IDEA'
      : approved ? 'APPROVE_MINIMAL_METHOD_REVISION' : 'REJECT_METHOD_REVISION';
    task.events.push({ id: randomUUID(), at: new Date().toISOString(), kind: 'state', text: `已记录人工决定：${decision} · ${revisionId}` });
    task.status = 'queued';
    task.threadRetryCount = 0;
    task.currentActivity = approved ? '已批准，等待 Codex 继续' : '已拒绝，等待 Codex 处理';
    task.review = null;
    task.pendingDecision = { decision, revisionId };
    task.decisionInFlight = { decision, revisionId };
    await saveState();
    broadcast();
    void drainQueue();
    sendJson(response, 200, publicTask(task));
    return;
  }
  sendJson(response, 404, { error: '接口不存在' });
}

await loadState();
await saveState();
createServer((request, response) => {
  handleRequest(request, response).catch((error) => {
    sendJson(response, 500, { error: error instanceof Error ? error.message : '服务错误' });
  });
}).listen(port, '127.0.0.1', () => {
  process.stdout.write(`The ThAInker Autodesign 本地服务已启动：http://127.0.0.1:${port}\n`);
  process.stdout.write(`工作区：${workspaceRoot}\n`);
  process.stdout.write(`任务并发数：${maxConcurrentTasks}\n`);
});

const artifactPollTimer = setInterval(() => {
  void Promise.all(tasks.map((task) => syncArtifacts(task)));
}, 5_000);
artifactPollTimer.unref();

const remoteGpuPollTimer = setInterval(() => {
  void refreshRemoteGpu();
}, 10_000);
remoteGpuPollTimer.unref();

void refreshRemoteGpu();
void drainQueue();
