export type RemoteGpuProcess = {
  pid: number;
  processName: string;
  usedMemoryMiB: number;
  elapsed: string | null;
  taskLabel: string;
};

export type RemoteGpu = {
  index: number;
  uuid: string;
  name: string;
  usedMemoryMiB: number;
  totalMemoryMiB: number;
  utilizationPercent: number;
  temperatureCelsius: number;
  processes: RemoteGpuProcess[];
};

export type RemoteGpuSnapshot = {
  status: 'loading' | 'connected' | 'stale' | 'unavailable';
  host: string;
  checkedAt: string | null;
  lastSuccessfulAt: string | null;
  gpus: RemoteGpu[];
  message: string;
};

function csvRows(value: string) {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.split(',').map((field) => field.trim()));
}

function taskLabel(processName: string, command: string) {
  const variant = command.match(/--variant\s+([^\s]+)/)?.[1];
  const seed = command.match(/--seed\s+(\d+)/)?.[1];
  const unit = variant && seed ? `${variant}/${seed}` : null;
  if (/\bmask-one\b/.test(command)) return unit ? `M1 遮挡 · ${unit}` : 'M1 遮挡实验';
  if (/\bpredict-one\b/.test(command)) return unit ? `M1 预测 · ${unit}` : 'M1 正常预测';
  if (/formal_train\.py/.test(command)) return unit ? `正式训练 · ${unit}` : '正式训练';
  if (/formal_eval\.py/.test(command)) return unit ? `正式评测 · ${unit}` : '正式评测';
  return processName || '计算进程';
}

function processDetails(psOutput: string) {
  const details = new Map<number, { elapsed: string; command: string }>();
  for (const line of psOutput.split('\n')) {
    const match = line.trim().match(/^(\d+)\s+(\S+)\s+(.+)$/);
    if (!match) continue;
    details.set(Number(match[1]), { elapsed: match[2], command: match[3] });
  }
  return details;
}

export function processIdsFromCsv(processCsv: string) {
  return csvRows(processCsv)
    .map((row) => Number(row[1]))
    .filter((pid) => Number.isInteger(pid) && pid > 0);
}

export function parseRemoteGpuSnapshot(
  host: string,
  checkedAt: string,
  gpuCsv: string,
  processCsv: string,
  psOutput: string,
): RemoteGpuSnapshot {
  const details = processDetails(psOutput);
  const processesByUuid = new Map<string, RemoteGpuProcess[]>();
  for (const [uuid, pidValue, processName, usedMemoryValue] of csvRows(processCsv)) {
    const pid = Number(pidValue);
    if (!uuid || !Number.isInteger(pid)) continue;
    const detail = details.get(pid);
    const process: RemoteGpuProcess = {
      pid,
      processName: processName || '计算进程',
      usedMemoryMiB: Number(usedMemoryValue) || 0,
      elapsed: detail?.elapsed || null,
      taskLabel: taskLabel(processName, detail?.command || ''),
    };
    processesByUuid.set(uuid, [...(processesByUuid.get(uuid) || []), process]);
  }

  const gpus = csvRows(gpuCsv).map(([index, uuid, name, usedMemory, totalMemory, utilization, temperature]) => ({
    index: Number(index),
    uuid,
    name,
    usedMemoryMiB: Number(usedMemory) || 0,
    totalMemoryMiB: Number(totalMemory) || 0,
    utilizationPercent: Number(utilization) || 0,
    temperatureCelsius: Number(temperature) || 0,
    processes: processesByUuid.get(uuid) || [],
  }));

  return {
    status: 'connected',
    host,
    checkedAt,
    lastSuccessfulAt: checkedAt,
    gpus,
    message: gpus.length ? '远端实时采样正常' : '远端已连接，但没有读取到 GPU',
  };
}
