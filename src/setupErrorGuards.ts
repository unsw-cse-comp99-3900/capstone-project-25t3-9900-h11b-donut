export function installErrorGuards() {
  if (typeof window === 'undefined') return;

  // 改进的错误处理：安全处理所有getBoundingClientRect错误
  window.addEventListener(
    'error',
    (e) => {
      const msg = String((e as ErrorEvent)?.message ?? '');

      
      // 安全处理所有getBoundingClientRect错误，包括内部错误
      if (msg.includes('getBoundingClientRect') || msg.includes('Cannot read properties of null')) {
        console.debug('[guard] Silenced getBoundingClientRect error:', msg);
        e.preventDefault();
        return;
      }
      
      // 对于其他内部错误，记录但不阻止
      console.warn('[guard] Error detected:', msg, e);
    },
    true
  );

  window.addEventListener(
    'unhandledrejection',
    (e) => {
      const reason = (e as PromiseRejectionEvent)?.reason;
      const msg =
        (typeof reason === 'string' && reason) ||
        (reason && reason.message) ||
        '';
      
      // 安全处理所有getBoundingClientRect相关的拒绝
      if (String(msg).includes('getBoundingClientRect') || String(msg).includes('Cannot read properties of null')) {
        console.debug('[guard] Silenced getBoundingClientRect rejection:', msg);
        e.preventDefault();
        return;
      }
      
      // 对于其他拒绝，记录但不阻止
      console.warn('[guard] Rejection detected:', msg);
    },
    true
  );
}