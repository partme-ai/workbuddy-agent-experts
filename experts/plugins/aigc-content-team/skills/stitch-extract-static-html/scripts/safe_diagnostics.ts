/** Format untrusted URLs for text and JSON diagnostics; never echo invalid input. */
export function safeUrl(value: string | null): string {
  try {
    const url = new URL(value ?? '');
    if (!['http:', 'https:'].includes(url.protocol)) return '[non-HTTP URL]';
    return `${url.protocol}//${url.host}${url.pathname}`;
  } catch {
    return '[invalid URL]';
  }
}

/** Error messages and stacks can contain credentials, page text and signed URLs. */
export function safeError(error: unknown): string {
  const code = error && typeof error === 'object' && 'code' in error ? error.code : undefined;
  const allowed = ['ENOTFOUND', 'EAI_AGAIN', 'ECONNREFUSED', 'ECONNRESET', 'ETIMEDOUT', 'ENOENT', 'EACCES'];
  return typeof code === 'string' && allowed.includes(code) ? code : 'operation failed';
}
