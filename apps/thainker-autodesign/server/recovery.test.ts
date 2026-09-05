import assert from 'node:assert/strict';
import test from 'node:test';
import { isRecoverableTransportDisconnect } from './recovery';

test('recognizes the Codex TLS stream disconnect as recoverable transport failure', () => {
  assert.equal(isRecoverableTransportDisconnect(
    'Reconnecting... 2/5 (stream disconnected before completion: IO error: peer closed connection without sending TLS close_notify)',
  ), true);
});

test('recognizes supported SSH and request transport failures', () => {
  assert.equal(isRecoverableTransportDisconnect('Connection reset by peer'), true);
  assert.equal(isRecoverableTransportDisconnect('request timed out while waiting for response'), true);
});

test('does not hide a real experiment or contract failure behind reconnect', () => {
  assert.equal(isRecoverableTransportDisconnect('result contract validation failed for seed 79'), false);
  assert.equal(isRecoverableTransportDisconnect('training command exited with code 1'), false);
});
