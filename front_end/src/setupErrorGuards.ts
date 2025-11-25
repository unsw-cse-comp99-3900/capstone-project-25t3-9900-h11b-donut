export function installErrorGuards() {
  if (typeof window === 'undefined') return;

  // Improved error handling: Safely handle all getBoundingClientRect errors
  window.addEventListener(
    'error',
    (e) => {
      const msg = String((e as ErrorEvent)?.message ?? '');

      
      // Safely handle all getBoundingClientRect errors, including internal errors
      if (msg.includes('getBoundingClientRect') || msg.includes('Cannot read properties of null')) {
        // Record more detailed context to help locate the source file and line numbers
        const err = e as ErrorEvent;
        console.error('[guard] getBoundingClientRect error:', msg, {
          filename: err.filename,
          lineno: err.lineno,
          colno: err.colno,
          stack: (err.error && (err.error as any).stack) || 'no stack'
        });
        e.preventDefault();
        return;
      }
      
      // For other internal errors, record but do not prevent them
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
      
      // Safely handle all rejections related to getBoundingClientRect
      if (String(msg).includes('getBoundingClientRect') || String(msg).includes('Cannot read properties of null')) {
        console.debug('[guard] Silenced getBoundingClientRect rejection:', msg);
        e.preventDefault();
        return;
      }
      
      // For other rejections, record but do not prevent
      console.warn('[guard] Rejection detected:', msg);
    },
    true
  );
}