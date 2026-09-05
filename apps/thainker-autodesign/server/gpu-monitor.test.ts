import assert from 'node:assert/strict';
import test from 'node:test';
import { parseRemoteGpuSnapshot, processIdsFromCsv } from './gpu-monitor';

const processCsv = [
  'GPU-0, 410190, python3, 3328',
  'GPU-1, 410189, python3, 3328',
].join('\n');

test('parses real nvidia-smi output and converts commands into experiment units', () => {
  const snapshot = parseRemoteGpuSnapshot(
    'connect.westd.seetacloud.com:45017',
    '2026-08-29T15:30:00.000Z',
    [
      '0, GPU-0, NVIDIA RTX PRO 6000 Blackwell Server Edition, 3337, 97887, 47, 44',
      '1, GPU-1, NVIDIA RTX PRO 6000 Blackwell Server Edition, 3337, 97887, 0, 43',
    ].join('\n'),
    processCsv,
    [
      '410189 01:18:51 python3 generated_project/formal_eval.py mask-one --variant mtl_global --seed 29',
      '410190 01:18:51 python3 generated_project/formal_eval.py mask-one --variant mtl_global --seed 17',
    ].join('\n'),
  );

  assert.equal(snapshot.status, 'connected');
  assert.equal(snapshot.gpus.length, 2);
  assert.deepEqual(snapshot.gpus[0].processes[0], {
    pid: 410190,
    processName: 'python3',
    usedMemoryMiB: 3328,
    elapsed: '01:18:51',
    taskLabel: 'M1 遮挡 · mtl_global/17',
  });
  assert.equal(snapshot.gpus[1].utilizationPercent, 0);
  assert.equal(snapshot.gpus[1].processes[0].taskLabel, 'M1 遮挡 · mtl_global/29');
});

test('extracts only numeric compute PIDs for the follow-up process query', () => {
  assert.deepEqual(processIdsFromCsv(processCsv), [410190, 410189]);
  assert.deepEqual(processIdsFromCsv(''), []);
});
