'use client';

import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from 'react';

type View = 'pipeline' | 'plan' | 'results';
type TaskStatus = 'queued' | 'waiting_thread' | 'reconnecting' | 'running' | 'pausing' | 'paused' | 'ready' | 'waiting_review' | 'reported' | 'completed' | 'failed' | 'abandoned';
type TaskSource = 'idea' | 'existing';

type Review = {
  revisionId: string;
  question: string;
  background: string;
  modification: string;
  rationale: string;
  validation: string;
  languageReady: boolean;
  atLimit: boolean;
};

type TaskEvent = {
  id: string;
  at: string;
  kind: 'state' | 'message' | 'command' | 'file' | 'error';
  text: string;
};

type ProgressCount = {
  completed: number;
  total: number;
};

type FormalProgressSnapshot = {
  mode?: 'formal_v1' | 'revision';
  training: ProgressCount | null;
  prediction: ProgressCount | null;
  masking: ProgressCount | null;
  externalPrediction?: ProgressCount | null;
  externalMasking?: ProgressCount | null;
  currentLabel?: string | null;
  currentUnits?: string[];
  currentPair?: number | null;
  maskPair?: number | null;
  snapshotComplete?: boolean;
};

type RemoteGpuProcess = {
  pid: number;
  processName: string;
  usedMemoryMiB: number;
  elapsed: string | null;
  taskLabel: string;
};

type RemoteGpu = {
  index: number;
  uuid: string;
  name: string;
  usedMemoryMiB: number;
  totalMemoryMiB: number;
  utilizationPercent: number;
  temperatureCelsius: number;
  processes: RemoteGpuProcess[];
};

type RemoteGpuSnapshot = {
  status: 'loading' | 'connected' | 'stale' | 'unavailable';
  host: string;
  checkedAt: string | null;
  lastSuccessfulAt: string | null;
  gpus: RemoteGpu[];
  message: string;
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
  runDir: string;
  workingDirectory: string;
  imported: boolean;
  currentActivity: string;
  latestArtifact: string | null;
  review: Review | null;
  results: TaskResults | null;
  formalProgress: FormalProgressSnapshot | null;
  plan: TaskPlan | null;
  createdAt: string;
  updatedAt: string;
  events: TaskEvent[];
};

const apiBase = process.env.NEXT_PUBLIC_AUTODESIGN_API || 'http://127.0.0.1:4317';

const stageLabels = [
  ['Idea 解析', '锁定科学输入'],
  ['证据梳理', '检索与基准选择'],
  ['实验设计', '组合与预期效应'],
  ['R0 验证', '低成本不确定性验证'],
  ['正式实验', '主实验与消融实验'],
  ['结果与审计', '结论与证据来源'],
];

const stageIndex: Record<string, number> = {
  INPUT_READY: 0,
  EXPERIMENT_DESIGN_READY: 2,
  WAITING_FOR_R0: 3,
  R0_PASSED: 3,
  R0_FAILED_RETURN_TO_DESIGN: 2,
  WAITING_FOR_METHOD_REVISION_APPROVAL: 2,
  DESIGN_REVISION_IN_PROGRESS: 2,
  IMPLEMENTATION_READY: 4,
  EXECUTION_IN_PROGRESS: 4,
  EXECUTION_PAUSED_BY_USER: 4,
  EXECUTION_COMPLETE: 4,
  RESULT_DIAGNOSIS_READY: 5,
  INTEGRITY_AUDIT_PASS: 5,
  INTEGRITY_AUDIT_FAIL: 5,
  COMPLETE: 5,
  IDEA_ABANDONED: 5,
};

const statusCopy: Record<TaskStatus, string> = {
  queued: '排队中',
  waiting_thread: '等待接续',
  reconnecting: '自动重连',
  running: '运行中',
  pausing: '正在暂停',
  paused: '已暂停',
  ready: '待诊断',
  waiting_review: '待审核',
  reported: '保守报告',
  completed: '已完成',
  failed: '失败',
  abandoned: '已废弃',
};

const sampleIdea = `# 未见任务族下的语义技能路由

## 研究动机
现有多模态技能路由通常在与技能开发任务族重叠的任务上评估，无法判断路由能力能否迁移到真正未见的任务族。

## 核心贡献
提出一种任务族感知的技能路由方法，将可复用的仪器读数能力与任务特定提示模式分离。

## 预期证据
任务族留出直接对比、路由消融、错误分层和定性轨迹。`;

const eventTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: 'Asia/Shanghai',
});

const snapshotTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
  timeZone: 'Asia/Shanghai',
});

function eventTime(value: string) {
  return eventTimeFormatter.format(new Date(value));
}

function snapshotTime(value: string | null) {
  return value ? snapshotTimeFormatter.format(new Date(value)) : '等待首次采样';
}

function gpuMemory(value: number) {
  return value >= 1024 ? `${(value / 1024).toFixed(1)} GB` : `${value} MiB`;
}

function resultNumber(value: number | null) {
  if (value === null) return '未提供';
  return Number.isInteger(value) ? String(value) : value.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
}

function meaningfulEvent(event: TaskEvent) {
  if (event.kind === 'command') return false;
  if (event.text.startsWith('Skill descriptions were shortened')) return false;
  return true;
}

function displayEventText(event: TaskEvent) {
  if (event.kind === 'error' && event.text.includes('already has an active writer')) {
    return '源 Codex 任务被桌面端占用，系统正在改用独立执行任务接续。';
  }
  if (event.kind === 'file' && event.text.includes('AUTODESIGN_STATE.md')) {
    return '实验状态与断点记录已更新。';
  }
  return event.text.replaceAll('`', '').trim();
}

function latestProgressCount(events: TaskEvent[], keyword: RegExp): ProgressCount | null {
  for (const event of [...events].reverse()) {
    if (!meaningfulEvent(event)) continue;
    const text = displayEventText(event);
    const before = text.match(new RegExp(`(\\d+)\\s*\\/\\s*(\\d+)[^。；\\n]{0,40}${keyword.source}`, 'i'));
    const after = text.match(new RegExp(`${keyword.source}[^。；\\n]{0,40}?(\\d+)\\s*\\/\\s*(\\d+)`, 'i'));
    const match = before || after;
    if (match) return { completed: Number(match[1]), total: Number(match[2]) };
  }
  return null;
}

function phaseState(progress: ProgressCount | null, active: boolean) {
  if (progress?.total && progress.completed >= progress.total) return 'done';
  if (progress || active) return 'active';
  return 'waiting';
}

function formalPhaseLabel(value: string | null | undefined) {
  const labels: Record<string, string> = {
    M1_mask: 'M1 遮挡实验',
    M2_external_predict: 'M2 外部预测',
    M2_external_mask: 'M2 外部遮挡',
    result_analysis: '结果汇总与诊断',
    method_revision_review: '方法修改审核',
    design_revision: '已批准，正在修订实验设计',
  };
  if (!value) return null;
  const completedPair = value.match(/formal training pair\s*(\d+)\s*\/\s*(\d+)\s*complete.*pair\s*(\d+)/i);
  if (completedPair) return `修订训练第 ${completedPair[1]} / ${completedPair[2]} 对已完成，正在检查第 ${completedPair[3]} 对恢复点`;
  const runningPair = value.match(/formal training pair\s*(\d+)\s*\/\s*(\d+)/i);
  if (runningPair) return `修订训练第 ${runningPair[1]} / ${runningPair[2]} 对`;
  return labels[value] || value;
}

const familyCopy: Record<ResultAggregate['family'], string> = {
  main: '主实验',
  ablation: '消融实验',
  case_study: '案例分析',
  analysis: '分析实验',
};

const planFamilyMeta: Record<PlanFamily, { label: string; purpose: string }> = {
  main: { label: '主实验', purpose: '直接检验总体方法是否成立，并与公平基线形成论文主要结果。' },
  ablation: { label: '消融实验', purpose: '逐项改变核心组件，判断性能和行为变化具体来自哪一部分。' },
  case_study: { label: 'Case Study', purpose: '用预先定义的成功、失败和副作用案例展示方法在具体样本上的行为。' },
  analysis: { label: '分析实验', purpose: '解释机制、风险、稳健性与适用边界，补足主结果无法回答的问题。' },
};

const planFamilyOrder: PlanFamily[] = ['main', 'ablation', 'case_study', 'analysis'];

export default function Home() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [tasks, setTasks] = useState<ExperimentTask[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [connected, setConnected] = useState(false);
  const [pauseSupported, setPauseSupported] = useState(false);
  const [remoteGpu, setRemoteGpu] = useState<RemoteGpuSnapshot | null>(null);
  const [view, setView] = useState<View>('pipeline');
  const [taskbarCollapsed, setTaskbarCollapsed] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [taskSource, setTaskSource] = useState<TaskSource>('idea');
  const [dragging, setDragging] = useState(false);
  const [ideaName, setIdeaName] = useState('idea.md');
  const [ideaText, setIdeaText] = useState('');
  const [newTaskWorkingDirectory, setNewTaskWorkingDirectory] = useState('');
  const [threadReference, setThreadReference] = useState('');
  const [workingDirectory, setWorkingDirectory] = useState('');
  const [importTitle, setImportTitle] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showAllEvents, setShowAllEvents] = useState(false);

  useEffect(() => {
    let alive = true;
    fetch(`${apiBase}/api/tasks`)
      .then(async (response) => {
        if (!response.ok) throw new Error('服务不可用');
        return await response.json() as ExperimentTask[];
      })
      .then((data) => {
        if (!alive) return;
        setConnected(true);
        setTasks(data);
        setSelectedId((current) => data.some((task) => task.id === current) ? current : data[0]?.id || '');
      })
      .catch(() => setConnected(false));
    fetch(`${apiBase}/api/health`)
      .then(async (response) => response.ok ? await response.json() as { workspaceRoot?: string; capabilities?: { pause?: boolean } } : null)
      .then((health) => {
        if (!alive) return;
        setPauseSupported(health?.capabilities?.pause === true);
        if (health?.workspaceRoot) setNewTaskWorkingDirectory((current) => current || health.workspaceRoot || '');
      })
      .catch(() => setPauseSupported(false));
    fetch(`${apiBase}/api/gpu`)
      .then(async (response) => {
        if (!response.ok) throw new Error('GPU 监控尚未启用');
        return await response.json() as RemoteGpuSnapshot;
      })
      .then((snapshot) => {
        if (alive) setRemoteGpu(snapshot);
      })
      .catch(() => undefined);
    const source = new EventSource(`${apiBase}/api/events`);
    source.addEventListener('tasks', (event) => {
      const data = JSON.parse((event as MessageEvent).data) as ExperimentTask[];
      setConnected(true);
      setTasks(data);
      setSelectedId((current) => data.some((task) => task.id === current) ? current : data[0]?.id || '');
    });
    source.addEventListener('gpu', (event) => {
      setRemoteGpu(JSON.parse((event as MessageEvent).data) as RemoteGpuSnapshot);
    });
    source.onerror = () => setConnected(false);
    return () => {
      alive = false;
      source.close();
    };
  }, []);

  const task = tasks.find((item) => item.id === selectedId) || tasks[0];
  const planGroups = planFamilyOrder.map((family) => ({
    family,
    experiments: task?.plan?.experiments.filter((experiment) => experiment.family === family) || [],
  }));
  const pauseDrainPending = Boolean(
    task?.status === 'paused' && /当前单元.*收尾|在途单元.*运行|完成前.*继续/.test(task.currentActivity),
  );
  const activeIndex = task ? stageIndex[task.stage] ?? 0 : 0;
  const stages = useMemo(() => stageLabels.map(([name, description], index) => ({
    id: String(index + 1).padStart(2, '0'),
    name,
    description,
    meta: index < activeIndex ? '已完成' : index === activeIndex ? task?.stageLabel || '进行中' : '等待中',
    state: index < activeIndex ? 'done' : index === activeIndex ? 'active' : 'waiting',
  })), [activeIndex, task?.stageLabel]);

  const counts = useMemo(() => ({
    running: tasks.filter((item) => item.status === 'running' || item.status === 'pausing' || item.status === 'reconnecting').length,
    review: tasks.filter((item) => item.status === 'waiting_review').length,
    queued: tasks.filter((item) => item.status === 'queued' || item.status === 'waiting_thread').length,
    paused: tasks.filter((item) => item.status === 'paused').length,
    ready: tasks.filter((item) => item.status === 'ready').length,
    reported: tasks.filter((item) => item.status === 'reported').length,
  }), [tasks]);

  const meaningfulEvents = useMemo(
    () => task ? task.events.filter(meaningfulEvent) : [],
    [task],
  );
  const visibleActivity = task?.currentActivity
    || (meaningfulEvents.length ? displayEventText(meaningfulEvents[meaningfulEvents.length - 1]) : '');
  const formalProgress = useMemo(() => {
    if (!task) return null;
    const snapshot = task.formalProgress;
    const revisionMode = snapshot?.mode === 'revision';
    const training = snapshot?.training || latestProgressCount(task.events, /(?:正式)?训练/);
    const prediction = snapshot?.prediction || latestProgressCount(task.events, /(?:M1\s*)?(?:域内|正常)?预测/);
    const masking = snapshot?.masking || latestProgressCount(task.events, /(?:M1\s*)?遮挡/);
    const externalPrediction = snapshot?.externalPrediction || latestProgressCount(task.events, /(?:M2\s*)?(?:外部|external)\s*(?:预测|prediction)/);
    const externalMasking = snapshot?.externalMasking || latestProgressCount(task.events, /(?:M2\s*)?(?:外部|external)\s*(?:遮挡|mask)/);
    const text = task.events.filter(meaningfulEvent).map(displayEventText).join('\n');
    const eventUnits = [...new Set(Array.from(text.matchAll(/\b([a-z][a-z0-9_]+\/\d+)\b/gi), (match) => match[1]))].slice(-2);
    const units = snapshot?.snapshotComplete
      ? []
      : snapshot?.currentUnits?.length ? snapshot.currentUnits : eventUnits;
    const maskPairMatches = Array.from(text.matchAll(/(?:M1\s*)?(?:mask|遮挡)[^。；\n]{0,50}?pair\s*(\d+)|pair\s*(\d+)[^。；\n]{0,50}?(?:mask|遮挡)/gi));
    const eventMaskPair = Number(maskPairMatches.at(-1)?.[1] || maskPairMatches.at(-1)?.[2] || 0) || null;
    const currentPair = snapshot?.snapshotComplete
      ? null
      : snapshot?.currentPair || snapshot?.maskPair || eventMaskPair;
    const maskingActive = task.stage === 'EXECUTION_IN_PROGRESS' && /(?:M1\s*)?(?:mask|遮挡)/i.test(text);
    if (!training && !prediction && !masking && !externalPrediction && !externalMasking && !['EXECUTION_IN_PROGRESS', 'EXECUTION_COMPLETE'].includes(task.stage)) return null;
    const currentLabel = formalPhaseLabel(snapshot?.currentLabel) || (maskingActive ? 'M1 遮挡实验' : null);
    const allFormalUnitsComplete = Boolean(snapshot?.snapshotComplete
      && training && prediction && masking
      && (revisionMode || (externalPrediction && externalMasking)));
    const headline = task.stage === 'EXECUTION_COMPLETE'
      ? '正式实验已完成，等待结果诊断'
      : allFormalUnitsComplete
        ? '正式实验单元已全部完成，正在汇总、诊断与审计'
      : revisionMode && currentLabel
        ? `当前：${currentLabel}`
      : currentLabel === 'M1 遮挡实验' && masking
      ? `当前：${currentLabel} ${masking.completed} / ${masking.total}`
      : currentLabel && currentPair
        ? `当前：${currentLabel}第 ${currentPair} 对`
        : currentLabel
          ? `当前：${currentLabel}`
          : masking
            ? `M1 遮挡实验 ${masking.completed} / ${masking.total}`
            : currentPair
              ? `当前：正式实验第 ${currentPair} 对`
              : '正在进入正式实验';
    const m1Complete = Boolean(masking?.total && masking.completed >= masking.total);
    const externalPredictionActive = currentLabel === 'M2 外部预测';
    const externalPredictionComplete = Boolean(externalPrediction?.total && externalPrediction.completed >= externalPrediction.total);
    const externalMaskingActive = currentLabel === 'M2 外部遮挡';
    return {
      training,
      prediction,
      masking,
      externalPrediction,
      externalMasking,
      currentPair,
      currentLabel,
      headline,
      units,
      artifactBacked: Boolean(snapshot),
      revisionMode,
      phases: [
        { label: revisionMode ? '修订训练' : '正式训练', progress: training, state: training ? phaseState(training, false) : maskingActive ? 'done' : 'waiting' },
        { label: revisionMode ? '修订预测' : 'M1 正常预测', progress: prediction, state: prediction ? phaseState(prediction, !training) : maskingActive ? 'done' : 'waiting' },
        { label: revisionMode ? '配对评估' : 'M1 遮挡实验', progress: masking, state: masking ? phaseState(masking, Boolean(prediction?.total && prediction.completed >= prediction.total)) : maskingActive ? 'active' : 'waiting' },
        ...(revisionMode ? [] : [
          { label: 'M2 外部预测', progress: externalPrediction, state: phaseState(externalPrediction, externalPredictionActive || m1Complete) },
          { label: 'M2 外部遮挡', progress: externalMasking, state: phaseState(externalMasking, externalMaskingActive || externalPredictionComplete) },
        ]),
        {
          label: '汇总、诊断与审计',
          progress: null,
          state: task.stage === 'COMPLETE'
            ? 'done'
            : allFormalUnitsComplete || ['EXECUTION_COMPLETE', 'RESULT_DIAGNOSIS_READY', 'INTEGRITY_AUDIT_PASS'].includes(task.stage)
              ? 'active'
              : 'waiting',
        },
      ],
    };
  }, [task]);

  const loadFile = async (file?: File) => {
    if (!file) return;
    setIdeaName(file.name);
    setIdeaText(await file.text());
  };

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => loadFile(event.target.files?.[0]);
  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    loadFile(event.dataTransfer.files?.[0]);
  };

  const useSample = () => {
    setIdeaName('semantic-skill-routing.md');
    setIdeaText(sampleIdea);
  };

  const startRun = async () => {
    if (!ideaText || !newTaskWorkingDirectory.trim() || submitting) return;
    if (!connected) {
      setFormError('本地执行服务未连接，请先启动服务后再提交任务。');
      return;
    }
    setSubmitting(true);
    setFormError('');
    try {
      const response = await fetch(`${apiBase}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileName: ideaName,
          ideaMarkdown: ideaText,
          workingDirectory: newTaskWorkingDirectory.trim(),
        }),
      });
      const data = await response.json() as ExperimentTask & { error?: string };
      if (!response.ok) throw new Error(data.error || '任务创建失败');
      setSelectedId(data.id);
      setUploadOpen(false);
      setView('pipeline');
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '任务创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const importTask = async () => {
    if (!connected || !apiBase || !threadReference.trim() || !workingDirectory.trim() || submitting) return;
    setSubmitting(true);
    setFormError('');
    try {
      const response = await fetch(`${apiBase}/api/tasks/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threadReference, workingDirectory, title: importTitle }),
      });
      const data = await response.json() as ExperimentTask & { error?: string };
      if (!response.ok) throw new Error(data.error || '任务导入失败');
      setSelectedId(data.id);
      setUploadOpen(false);
      setView('pipeline');
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '任务导入失败');
    } finally {
      setSubmitting(false);
    }
  };

  const resumeTask = async () => {
    if (!task || !['paused', 'ready'].includes(task.status) || !connected || !apiBase) return;
    const response = await fetch(`${apiBase}/api/tasks/${task.id}/resume`, { method: 'POST' });
    if (!response.ok) {
      const data = await response.json() as { error?: string };
      setFormError(data.error || '无法继续该任务');
    }
  };

  const pauseTask = async () => {
    if (!task || !['running', 'waiting_thread', 'reconnecting'].includes(task.status) || !connected || !apiBase) return;
    const response = await fetch(`${apiBase}/api/tasks/${task.id}/pause`, { method: 'POST' });
    if (!response.ok) {
      const data = await response.json() as { error?: string };
      setFormError(data.error || '无法暂停该任务');
    }
  };

  const decide = async (approved: boolean) => {
    if (!task?.review) return;
    if (connected && apiBase) {
      const response = await fetch(`${apiBase}/api/tasks/${task.id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, revisionId: task.review.revisionId }),
      });
      const data = await response.json() as ExperimentTask & { error?: string };
      if (!response.ok) {
        setFormError(data.error || '人工决定提交失败');
        return;
      }
      setTasks((current) => current.map((item) => item.id === data.id ? data : item));
      return;
    }
    setTasks((current) => current.map((item) => item.id === task.id ? {
      ...item,
      status: approved ? 'running' : task.review?.atLimit ? 'abandoned' : 'running',
      stage: approved ? 'WAITING_FOR_R0' : task.review?.atLimit ? 'IDEA_ABANDONED' : 'R0_FAILED_RETURN_TO_DESIGN',
      stageLabel: approved ? 'R0 验证' : task.review?.atLimit ? 'Idea 已废弃' : '重新设计',
      progress: approved ? 48 : task.review?.atLimit ? 100 : 36,
      currentActivity: approved ? '已记录批准，Codex 正在登记 R0 验证' : task.review?.atLimit ? '已记录 No，当前 Idea 已废弃' : '已记录拒绝，Codex 正在寻找另一条设计路径',
      review: null,
    } : item));
  };

  const uploadDialog = uploadOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setUploadOpen(false); }}>
    <section className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
      <div className="modal-head"><div><span className="section-label">实验任务入口</span><h2 id="upload-title">{taskSource === 'idea' ? '提交 idea.md' : '接续已有任务'}</h2></div><button aria-label="关闭窗口" onClick={() => setUploadOpen(false)}>×</button></div>
      <div className="task-source-tabs" role="tablist" aria-label="任务来源"><button className={taskSource === 'idea' ? 'selected' : ''} onClick={() => { setTaskSource('idea'); setFormError(''); }}>上传 idea.md</button><button className={taskSource === 'existing' ? 'selected' : ''} onClick={() => { setTaskSource('existing'); setFormError(''); }}>接续已有任务</button></div>
      {taskSource === 'idea' ? <>
        <p className="modal-copy">研究动机和核心贡献为必填项。请同时指定实验项目目录；Codex 将在该项目内工作，任务产物也写入该项目。</p>
        {!connected && <div className="demo-warning">当前没有连接本地执行服务，请先启动本地服务后再提交任务。</div>}
        <div className="existing-task-form new-task-project-form">
          <label><span>实验项目目录</span><input value={newTaskWorkingDirectory} onChange={(event) => setNewTaskWorkingDirectory(event.target.value)} placeholder="/Users/yzb/Desktop/research/exp39" /></label>
        </div>
        <div className="import-note project-location-note"><strong>产物保存位置</strong><span>{newTaskWorkingDirectory.trim() ? `${newTaskWorkingDirectory.trim()}/assets/output/thainker_<任务编号>/` : '填写项目目录后显示'}</span></div>
        <input ref={inputRef} type="file" accept=".md,text/markdown,text/plain" onChange={onFileChange} hidden />
        <div className={`drop-zone ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop} onClick={() => inputRef.current?.click()}>
          <span className="file-glyph">MD</span>
          <strong>{ideaText ? ideaName : '将 idea.md 拖到这里'}</strong>
          <small>{ideaText ? `已载入 ${ideaText.length.toLocaleString()} 个字符` : '也可以点击选择 Markdown 文件'}</small>
        </div>
        {ideaText && <pre className="idea-preview">{ideaText}</pre>}
        <div className="modal-actions"><button className="sample-button" onClick={useSample}>填入示例 idea</button><button className="start-button" disabled={!connected || !ideaText || !newTaskWorkingDirectory.trim() || submitting} onClick={startRun}>{submitting ? '正在创建任务' : connected ? '交给 Codex 执行' : '等待本地服务'} <span>→</span></button></div>
      </> : <>
        <p className="modal-copy">输入原 Codex 任务链接和它的实验目录。导入只读取现有状态并显示在任务栏，不会立即恢复实验。</p>
        {!connected && <div className="demo-warning">接续已有任务需要连接本地执行服务。</div>}
        <div className="existing-task-form">
          <label><span>Codex 任务链接或 thread ID</span><input value={threadReference} onChange={(event) => setThreadReference(event.target.value)} placeholder="codex://threads/01a03823-0593-7203-a379-c44be38c8d70" /></label>
          <label><span>实验所在目录</span><input value={workingDirectory} onChange={(event) => setWorkingDirectory(event.target.value)} placeholder="/Users/yzb/Desktop/research/exp40" /></label>
          <label><span>任务名称（可选）</span><input value={importTitle} onChange={(event) => setImportTitle(event.target.value)} placeholder="不填写时从 AUTODESIGN_STATE.md 生成" /></label>
        </div>
        <div className="import-note"><strong>导入后仍保持暂停</strong><span>只有你在任务页面点击“继续实验”，Codex 才会从原 thread 和原目录恢复。</span></div>
        <div className="modal-actions single"><button className="start-button" disabled={!connected || !threadReference.trim() || !workingDirectory.trim() || submitting} onClick={importTask}>{submitting ? '正在读取状态' : '导入但不继续'} <span>→</span></button></div>
      </>}
      {formError && <div className="form-error">{formError}</div>}
    </section>
  </div>;

  if (!task) {
    return <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">T</span>
          <span>The Th<span>AI</span>nker</span>
          <span className="brand-product">Autodesign</span>
        </div>
        <div className="topbar-actions">
          <span className={`agent-status ${connected ? 'connected' : 'demo'}`}><i />{connected ? '本地 Codex 已连接' : '本地服务未连接'}</span>
          <button className="upload-button" onClick={() => setUploadOpen(true)}>＋ 新建任务</button>
        </div>
      </header>

      <div className={`workspace empty-workspace ${taskbarCollapsed ? 'taskbar-collapsed' : ''}`}>
        <aside className={`taskbar ${taskbarCollapsed ? 'collapsed' : ''}`}>
          <div className="taskbar-head">
            <div><p>实验任务</p><strong>0</strong></div>
            <span className="taskbar-actions">
              <button className="taskbar-toggle" onClick={() => setTaskbarCollapsed((current) => !current)} aria-label={taskbarCollapsed ? '展开实验任务栏' : '折叠实验任务栏'} aria-expanded={!taskbarCollapsed} title={taskbarCollapsed ? '展开实验任务栏' : '折叠实验任务栏'}>{taskbarCollapsed ? '›' : '‹'}</button>
              <button onClick={() => setUploadOpen(true)} aria-label="新建任务" title="新建任务">＋</button>
            </span>
          </div>
          <div className="task-counts"><span><i className="running" />运行中 0</span><span><i className="paused" />已暂停 0</span><span><i className="review" />待审核 0</span><span><i />排队 0</span></div>
          <div className="task-list"><p className="empty-task-list">任务列表为空</p></div>
          <div className="queue-note"><strong>执行队列</strong><p>上传 idea.md 后，每项实验会创建独立的 Codex thread 和运行目录。</p></div>
        </aside>

        <section className="empty-workspace-panel">
          <div className="empty-workspace-card">
            <span className="section-label">开始第一个实验</span>
            <h1>还没有实验任务</h1>
            <p>上传一个 idea.md，系统会创建独立任务，并在这里展示实验设计、执行进度、人工审核断点和最终结果。</p>
            <button className="empty-upload-button" onClick={() => setUploadOpen(true)}>上传 idea.md <span>→</span></button>
            <div className="empty-pipeline" aria-label="实验流程预览">
              {stageLabels.map(([name], index) => <span key={name}><i>{index + 1}</i>{name}</span>)}
            </div>
          </div>
        </section>
      </div>

      {uploadDialog}
    </main>;
  }

  const completed = stages.filter((stage) => stage.state === 'done').length;
  const isReview = task.status === 'waiting_review' && task.review;
  const conservativeReportReview = Boolean(task.review && /KZERO|K-?ZERO/i.test(task.review.revisionId));
  const latestEvents = (showAllEvents ? meaningfulEvents : meaningfulEvents.slice(-6)).toReversed();
  const actualResults = task.results?.aggregates || [];

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">T</span>
          <span>The Th<span>AI</span>nker</span>
          <span className="brand-product">Autodesign</span>
        </div>
        <div className="topbar-actions">
          <span className={`agent-status ${connected ? 'connected' : 'demo'}`}><i />{connected ? '本地 Codex 已连接' : '本地服务未连接'}</span>
          <button className="upload-button" onClick={() => setUploadOpen(true)}>＋ 新建任务</button>
        </div>
      </header>

      <div className={`workspace ${taskbarCollapsed ? 'taskbar-collapsed' : ''}`}>
        <aside className={`taskbar ${taskbarCollapsed ? 'collapsed' : ''}`}>
          <div className="taskbar-head">
            <div><p>实验任务</p><strong>{tasks.length}</strong></div>
            <span className="taskbar-actions">
              <button className="taskbar-toggle" onClick={() => setTaskbarCollapsed((current) => !current)} aria-label={taskbarCollapsed ? '展开实验任务栏' : '折叠实验任务栏'} aria-expanded={!taskbarCollapsed} title={taskbarCollapsed ? '展开实验任务栏' : '折叠实验任务栏'}>{taskbarCollapsed ? '›' : '‹'}</button>
              <button onClick={() => setUploadOpen(true)} aria-label="新建任务" title="新建任务">＋</button>
            </span>
          </div>
          <div className="task-counts">
            <span><i className="running" />运行中 {counts.running}</span>
            <span><i className="paused" />已暂停 {counts.paused}</span>
            <span><i className="ready" />待诊断 {counts.ready}</span>
            <span><i className="reported" />保守报告 {counts.reported}</span>
            <span><i className="review" />待审核 {counts.review}</span>
            <span><i />排队 {counts.queued}</span>
          </div>
          <div className="task-list">
            {tasks.map((item) => (
              <button className={`task-item ${selectedId === item.id ? 'selected' : ''}`} key={item.id} title={`${item.title} · ${statusCopy[item.status]}`} onClick={() => { setSelectedId(item.id); setView('pipeline'); }}>
                <span className={`status-dot ${item.status}`} />
                <span className="task-copy"><strong>{item.title}</strong><small>{item.stageLabel}</small></span>
                <span className="task-status">{statusCopy[item.status]}</span>
                <span className="task-progress"><i style={{ width: `${item.progress}%` }} /></span>
              </button>
            ))}
          </div>
          <div className="queue-note">
            <strong>执行队列</strong>
            <p>可同时管理多个任务。当前 GPU 策略默认一次执行一个完整实验；满足单卡隔离条件时可配置为两个。</p>
          </div>
        </aside>

        <aside className="stage-sidebar">
          <div className="sidebar-head"><p>当前任务流程</p><span>{task.progress}%</span></div>
          <h2>{task.title}</h2>
          <div className="run-id">{task.id.slice(0, 12)}</div>
          <nav aria-label="实验流程">
            {stages.map((stage) => (
              <button className={`nav-stage ${stage.state}`} key={stage.id} onClick={() => setView('pipeline')}>
                <span className="stage-index">{stage.state === 'done' ? '✓' : stage.id}</span>
                <span><strong>{stage.name}</strong><small>{stage.meta}</small></span>
              </button>
            ))}
          </nav>
          <div className="sidebar-foot">
            <p><span>执行环境</span><strong>{connected ? '本地 Codex' : '本地服务未连接'}</strong></p>
            <p><span>项目目录</span><strong>{task.workingDirectory}</strong></p>
            <p><span>任务目录</span><strong>{task.runDir}</strong></p>
          </div>
        </aside>

        <section className="main-panel">
          <div className="eyebrow-row"><span>自动实验设计 / {task.stageLabel}</span><span className={`live-pill ${task.status}`}><i />{statusCopy[task.status]}</span></div>
          <div className="title-row">
            <div><h1>{task.title}</h1><p>{task.imported ? <>
              接续源 Codex thread <b>{task.sourceThreadId || task.threadId}</b>
              {task.sourceThreadId && task.threadId !== task.sourceThreadId && <> · 当前执行 thread <b>{task.threadId}</b></>}
            </> : <>根据 <b>{task.fileName}</b> 创建的独立实验任务</>}</p></div>
          </div>

          <div className="view-tabs" role="tablist" aria-label="任务视图">
            {([['pipeline', '实时流程'], ['plan', '实验方案'], ['results', '实验结果']] as [View, string][]).map(([id, label]) => (
              <button key={id} className={view === id ? 'selected' : ''} onClick={() => setView(id)} role="tab" aria-selected={view === id}>{label}{id === 'results' && !connected && <span>未连接</span>}</button>
            ))}
          </div>

          {view === 'pipeline' && <>
            <div className="pipeline-card">
              <div className="pipeline-head"><span>流程进度</span><strong>已完成 {completed} / 6 个阶段</strong></div>
              <div className="pipeline-track">
                {stages.map((stage, index) => <div className={`track-node ${stage.state}`} key={stage.id}><span>{stage.state === 'done' ? '✓' : index + 1}</span><small>{stage.name}</small></div>)}
              </div>
              {formalProgress && <section className="formal-progress" aria-label="正式实验详细进度">
                <div className="formal-progress-head"><div><small>正式实验明细 · {formalProgress.artifactBacked ? '实验产物同步' : '实时任务状态'}</small><strong>{formalProgress.headline}</strong></div><span>{formalProgress.units.length ? `当前单元：${formalProgress.units.join('、')}` : '等待下一个实验单元'}</span></div>
                <div className={`formal-phase-grid ${formalProgress.revisionMode ? 'revision' : ''}`}>
                  {formalProgress.phases.map((phase) => {
                    const percent = phase.progress?.total ? Math.round(phase.progress.completed / phase.progress.total * 100) : phase.state === 'done' ? 100 : 0;
                    return <div className={`formal-phase ${phase.state}`} key={phase.label}><span><i />{phase.label}</span><strong>{phase.progress ? `${phase.progress.completed} / ${phase.progress.total}` : phase.state === 'done' ? '已完成' : phase.state === 'active' ? '运行中' : '等待'}</strong><div><i style={{ width: `${percent}%` }} /></div></div>;
                  })}
                </div>
              </section>}
            </div>

            <section className={`gpu-monitor ${remoteGpu?.status || 'unavailable'}`} aria-label="远端 GPU 资源监控">
              <div className="gpu-monitor-head">
                <div><small>远端资源监控</small><h2>GPU 与实验进程</h2></div>
                <div className="gpu-monitor-state">
                  <span><i />{remoteGpu?.status === 'connected' ? '实时连接' : remoteGpu?.status === 'stale' ? '显示上次采样' : remoteGpu?.status === 'loading' ? '正在读取' : '等待监控服务'}</span>
                  <small>{remoteGpu ? `${remoteGpu.host} · ${snapshotTime(remoteGpu.lastSuccessfulAt)}` : '本地服务安全重启后自动启用'}</small>
                </div>
              </div>
              {remoteGpu?.gpus.length ? <div className="gpu-grid">
                {remoteGpu.gpus.map((gpu) => {
                  const memoryPercent = gpu.totalMemoryMiB ? Math.min(100, Math.round(gpu.usedMemoryMiB / gpu.totalMemoryMiB * 100)) : 0;
                  return <article className={`gpu-card ${gpu.processes.length ? 'occupied' : 'idle'}`} key={gpu.uuid}>
                    <div className="gpu-card-head"><div><span>GPU {gpu.index}</span><strong>{gpu.name}</strong></div><em>{gpu.processes.length ? `${gpu.processes.length} 个计算进程` : '空闲'}</em></div>
                    <div className="gpu-metrics">
                      <div><small>显存</small><strong>{gpuMemory(gpu.usedMemoryMiB)} / {gpuMemory(gpu.totalMemoryMiB)}</strong><div><i style={{ width: `${memoryPercent}%` }} /></div></div>
                      <div><small>计算利用率</small><strong>{gpu.utilizationPercent}%</strong></div>
                      <div><small>温度</small><strong>{gpu.temperatureCelsius}°C</strong></div>
                    </div>
                    <div className="gpu-processes">
                      <small>任务占用</small>
                      {gpu.processes.length ? gpu.processes.map((process) => <div className="gpu-process" key={process.pid}><div><strong>{process.taskLabel}</strong><span>PID {process.pid}{process.elapsed ? ` · 已运行 ${process.elapsed}` : ''}</span></div><b>{gpuMemory(process.usedMemoryMiB)}</b></div>) : <p>当前没有 GPU 计算进程</p>}
                    </div>
                  </article>;
                })}
              </div> : <div className="gpu-monitor-empty"><strong>{remoteGpu?.message || '监控代码已就绪'}</strong><p>{remoteGpu ? '后端会继续自动重试远端只读采样。' : '当前实验不会被重启或打断；执行服务安全重启后，这里会自动显示真实 GPU 数据。'}</p></div>}
              <p className="gpu-monitor-note">显存、利用率和进程来自远端实时采样；它们用于确认资源确实被占用，实验结果是否有效仍以结果合同校验为准。</p>
            </section>

            <article className="codex-card">
              <div className="codex-card-head">
                <div className="codex-icon">C</div>
                <div><strong>{visibleActivity}</strong><p>{connected ? '只显示实验进展、结果和断点，不显示底层命令' : '当前显示的是最后一次同步的本地任务状态'}</p></div>
                <span className={`working-badge ${task.status}`}>{statusCopy[task.status]}</span>
              </div>
              <div className="activity-grid">
                <div><small>当前阶段</small><p>{task.stageLabel}</p></div>
                <div><small>当前子阶段</small><p>{formalProgress?.currentLabel || (formalProgress?.masking ? `M1 遮挡 ${formalProgress.masking.completed} / ${formalProgress.masking.total}` : task.stageLabel)}</p></div>
                <div><small>正在处理</small><p className="file-link">{formalProgress?.units.length ? formalProgress.units.join('、') : task.latestArtifact || '等待下一个节点'}</p></div>
              </div>
            </article>

            <section className="event-card">
              <div className="event-card-head"><div className="section-label">关键实验节点</div><span>共 {meaningfulEvents.length} 条</span></div>
              {latestEvents.length ? latestEvents.map((event) => (
                <div className="event-row" key={event.id}><time>{eventTime(event.at)}</time><span className={`event-kind ${event.kind}`}>{event.kind === 'file' ? '产物' : event.kind === 'error' ? '提醒' : event.kind === 'message' ? '进展' : '节点'}</span><p>{displayEventText(event)}</p></div>
              )) : <p className="empty-copy">等待第一个重要实验节点。</p>}
              {meaningfulEvents.length > 6 && <button className="event-history-button" onClick={() => setShowAllEvents((current) => !current)}>{showAllEvents ? '收起较早记录' : `查看更早记录（${meaningfulEvents.length - 6}）`}</button>}
            </section>
          </>}

          {view === 'plan' && <section className="plan-view">
            {task.plan ? <>
              <article className="plan-goal">
                <div className="plan-goal-head"><div><span className="section-label">总体目标</span><h2>{task.plan.ideaTitle}</h2></div><span>{task.plan.source === 'frontend_plan.json' ? '中文方案摘要' : task.plan.source === 'experiment_design.md' ? '读取真实实验方案' : '等待实验设计'}</span></div>
                <p>{task.plan.goal}</p>
                {task.plan.contributions.length > 0 && <div className="plan-contributions">
                  <strong>核心贡献</strong>
                  <div>{task.plan.contributions.map((contribution, index) => <p key={`${index}-${contribution}`}><span>C{index + 1}</span>{contribution}</p>)}</div>
                </div>}
              </article>

              {task.plan.experiments.length > 0 ? <div className="plan-families">
                {planGroups.map(({ family, experiments }) => {
                  const meta = planFamilyMeta[family];
                  return <section className="plan-family" key={family}>
                    <div className="plan-family-head"><div><span className="section-label">{meta.label}</span><h2>{meta.purpose}</h2></div><strong>{experiments.length} 项</strong></div>
                    {experiments.length > 0 ? <div className="plan-experiments">
                      {experiments.map((experiment) => <article className="plan-experiment" key={experiment.id}>
                        <div className="plan-experiment-head"><span>{experiment.id}</span><div><h3>{experiment.title}</h3><small>{experiment.evidenceClass === 'MECHANISM_PILOT' ? '机制 Pilot' : experiment.evidenceClass === 'ENGINEERING_SMOKE' ? '工程检查' : '结论证据'}</small></div></div>
                        {experiment.question && <div className="plan-detail plan-question"><strong>要回答的问题</strong><p>{experiment.question}</p></div>}
                        <div className="plan-detail-grid">
                          {experiment.comparison && <div className="plan-detail"><strong>比较与操作</strong><p>{experiment.comparison}</p></div>}
                          {experiment.display && <div className="plan-detail"><strong>主要展示</strong><p>{experiment.display}</p></div>}
                          {experiment.variants && <div className="plan-detail"><strong>实验变体</strong><p>{experiment.variants}</p></div>}
                          {experiment.claim && <div className="plan-detail"><strong>对应贡献</strong><p>{experiment.claim}</p></div>}
                        </div>
                      </article>)}
                    </div> : <p className="plan-family-empty">当前方案没有安排这一类实验。</p>}
                  </section>;
                })}
              </div> : <div className="plan-waiting"><strong>Idea 已读取，实验组合尚未生成</strong><p>Codex 完成 experiment_design.md 后，这里会自动出现主实验、消融、Case Study 和分析实验的真实内容。</p></div>}
            </> : <div className="plan-waiting"><strong>正在读取当前 Idea</strong><p>实验目标与方案生成后会同步到这里。</p></div>}
          </section>}

          {view === 'results' && <section className="results-view">
            {actualResults.length && task.results ? <>
              <div className="observed-banner"><strong>真实任务聚合结果</strong><span>已观测 {task.results.observedCellCount} / {task.results.expectedCellCount} 个计划单元 · 自动贡献结论保持 {task.results.automaticClaimVerdict}</span></div>
              <div className="results-head"><div><span className="section-label">任务结果</span><h2>主实验、消融与分析</h2></div><div className="result-verdict"><small>结果状态</small><strong>{task.results.status}</strong></div></div>
              <div className="actual-results">
                {(['main', 'ablation', 'case_study', 'analysis'] as ResultAggregate['family'][]).map((family) => {
                  const rows = actualResults.filter((result) => result.family === family);
                  if (!rows.length) return null;
                  return <section className="result-family" key={family}>
                    <div className="result-family-head"><strong>{familyCopy[family]}</strong><span>{rows.length} 条聚合结果</span></div>
                    <div className="actual-tr actual-th"><span>实验</span><span>变体</span><span>评测任务</span><span>指标</span><span>均值</span><span>标准差</span><span>样本数</span></div>
                    {rows.map((row) => <div className="actual-tr" key={`${row.experimentId}-${row.variantId}-${row.benchmarkTaskId}-${row.metric}`}><span>{row.experimentId}</span><span>{row.variantId}</span><span>{row.benchmarkTaskId}</span><span>{row.metric}</span><span>{resultNumber(row.mean)}</span><span>{resultNumber(row.sampleStd)}</span><span>{row.n}</span></div>)}
                  </section>;
                })}
              </div>
            </> : <>
              <div className="observed-banner"><strong>尚无可展示的聚合结果</strong><span>当前任务还没有产出 result_summary.json；这里不会填入示例数值</span></div>
              <div className="results-head"><div><span className="section-label">真实任务结果</span><h2>等待主实验、消融与分析完成</h2></div><div className="result-verdict"><small>当前状态</small><strong>{task.stageLabel}</strong></div></div>
              <section className="readiness"><span className="section-label">结果产物</span><div><i /> 主实验汇总 <b>等待任务</b></div><div><i /> 效应比较 <b>等待任务</b></div><div><i /> 结果诊断 <b>等待任务</b></div><div><i /> 完整性审计 <b>等待任务</b></div></section>
            </>}
          </section>}
        </section>

        <aside className={`decision-panel ${isReview ? '' : 'decision-resolved'}`}>
          {isReview && task.review ? <>
            <div className="decision-kicker"><span>!</span>需要人工判断</div>
            <h2>{task.review.question}</h2>
            <p className="decision-summary">这里只处理会改变方法或科学设计的断点。普通执行修复由 Codex 自动完成。</p>
            <div className="revision-id"><span>Revision ID</span><strong>{task.review.revisionId}</strong></div>
            <div className="proposal-block"><small>审核背景</small><p>{task.review.background}</p></div>
            <div className="proposal-block"><small>具体修改方法</small><p>{task.review.modification}</p></div>
            <div className="proposal-block"><small>设计思路</small><p>{task.review.rationale}</p></div>
            <div className="proposal-block validation"><small>实验验证、成本与回退</small><p>{task.review.validation}</p></div>
            {!task.review.languageReady && <div className="decision-note decision-warning">中文审核摘要不完整，系统已阻止提交。Codex 补齐四段中文说明后才会开放 Yes/No。</div>}
            <div className="decision-note">{conservativeReportReview ? 'Yes 将批准新 Revision 并继续实验；No 将不修改方法，采用当前保守报告并结束本轮。' : 'Yes 或 No 都会和当前 Revision ID 一起写入任务记录，未收到决定前不会修改已接受的方法。'}</div>
            <div className="decision-actions"><button className="reject" disabled={!task.review.languageReady} onClick={() => decide(false)}>No{task.review.atLimit ? '，废弃 Idea' : conservativeReportReview ? '，采用保守报告' : '，暂不批准'}</button><button className="approve" disabled={!task.review.languageReady} onClick={() => decide(true)}>Yes{task.review.atLimit ? '，批准例外' : '，批准并继续'} <span>→</span></button></div>
          </> : <>
            <div className="decision-kicker"><span>{task.status === 'completed' || task.status === 'reported' ? '✓' : task.status === 'failed' ? '!' : task.status === 'reconnecting' ? '↻' : task.status === 'paused' || task.status === 'pausing' ? 'Ⅱ' : task.status === 'ready' ? '→' : 'C'}</span>{task.status === 'reported' ? '保守报告已保存' : task.status === 'completed' ? '任务已完成' : task.status === 'failed' ? '任务执行失败' : task.status === 'reconnecting' ? 'Codex 自动重连' : task.status === 'waiting_thread' ? '等待 Codex 任务' : task.status === 'pausing' || pauseDrainPending ? '正在安全暂停' : task.status === 'paused' ? '实验已暂停' : task.status === 'ready' ? '正式实验已完成' : 'Codex 自动执行'}</div>
            <h2>{task.status === 'queued' ? '任务正在排队' : task.status === 'reconnecting' ? '连接中断，正在从已有产物恢复' : task.status === 'waiting_thread' ? '正在接续原实验' : task.status === 'pausing' || pauseDrainPending ? '正在等待当前单元完成' : task.status === 'paused' ? '可以接着原任务继续' : task.status === 'ready' ? '可以继续结果诊断与审计' : task.status === 'reported' ? '本轮已按保守结论结束' : task.status === 'completed' ? '实验结果已产出' : task.status === 'failed' ? '需要查看运行记录' : task.status === 'abandoned' ? '当前 Idea 已废弃' : '当前无需人工审核'}</h2>
            <p className="decision-summary">{task.currentActivity}</p>
            {task.status === 'running' && <button className="pause-button" disabled={!connected || !pauseSupported} onClick={pauseTask}>{pauseSupported ? '自动安全暂停' : '本地服务更新后可暂停'} <span>Ⅱ</span></button>}
            {task.status === 'waiting_thread' && <button className="pause-button" disabled={!connected || !pauseSupported} onClick={pauseTask}>取消重试并保持暂停 <span>Ⅱ</span></button>}
            {task.status === 'reconnecting' && <button className="pause-button" disabled={!connected || !pauseSupported} onClick={pauseTask}>取消重连并保持暂停 <span>Ⅱ</span></button>}
            {task.status === 'pausing' && <button className="pause-button pause-registered" disabled>后台正在自动收尾并确认暂停 <span>Ⅱ</span></button>}
            {task.status === 'paused' && <button className="resume-button" disabled={!connected || pauseDrainPending} onClick={resumeTask}>{pauseDrainPending ? '已登记：当前单元收尾中' : connected ? '继续实验' : '连接本地服务后可继续'} <span>{pauseDrainPending ? 'Ⅱ' : '→'}</span></button>}
            {task.status === 'ready' && <button className="resume-button" disabled={!connected} onClick={resumeTask}>{connected ? '继续结果诊断' : '连接本地服务后可继续'} <span>→</span></button>}
            <div className="resolved-graphic"><span>{activeIndex + 1}</span><div><small>当前阶段</small><strong>{stages[activeIndex].name}</strong></div></div>
            <div className="autonomy-list"><p><i /> 每个任务使用独立 Codex thread</p><p><i /> 暂停由后台自动收尾并确认</p><p><i /> 普通边界修复自动完成</p><p><i /> 科学方法修改必须返回 Yes 或 No</p></div>
          </>}
        </aside>
      </div>

      {uploadDialog}
    </main>
  );
}
