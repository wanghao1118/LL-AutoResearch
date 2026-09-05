const recoverableTransportPatterns = [
  /stream disconnected before completion/i,
  /peer closed connection without sending tls close_notify/i,
  /connection reset by peer/i,
  /broken pipe/i,
  /unexpected (?:end of file|eof)/i,
  /request timed out/i,
  /network error/i,
];

export function isRecoverableTransportDisconnect(message: string) {
  return recoverableTransportPatterns.some((pattern) => pattern.test(message));
}
