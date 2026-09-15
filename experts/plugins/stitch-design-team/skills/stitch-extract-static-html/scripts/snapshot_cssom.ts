/**
 * Materialize readable CSSOM sheets without losing their source context.
 * This function is self-contained so Puppeteer can serialize it into the page.
 */
export function materializeCssomStyles(targetDocument?: any): number {
  const document = targetDocument ?? (globalThis as any).document;
  let totalRules = 0;

  const resolveCssUrls = (cssText: string, sourceUrl: string): string =>
    cssText.replace(
      /url\(\s*(['"]?)([^'")\s]+)\1\s*\)/gi,
      (match: string, _quote: string, url: string) => {
        if (
          url.startsWith('data:') ||
          url.startsWith('http:') ||
          url.startsWith('https:') ||
          url.startsWith('//') ||
          url.startsWith('#')
        ) {
          return match;
        }
        try {
          return `url("${new URL(url, sourceUrl).href}")`;
        } catch {
          return match;
        }
      },
    );

  for (const sheet of Array.from(document.styleSheets) as any[]) {
    try {
      let sheetCss = '';
      const sourceUrl = sheet.href || document.baseURI;
      for (const rule of Array.from(sheet.cssRules) as any[]) {
        sheetCss += resolveCssUrls(rule.cssText, sourceUrl) + '\n';
        totalRules++;
      }
      if (!sheetCss.trim()) continue;

      const style = document.createElement('style');
      style.textContent = sheetCss;
      if (sheet.href) {
        style.setAttribute('data-source-url', sheet.href);
      }
      const mediaText = sheet.media?.mediaText?.trim();
      if (mediaText && mediaText !== 'all') {
        style.setAttribute('media', mediaText);
      }

      const owner = sheet.ownerNode;
      if (owner?.parentNode) {
        owner.parentNode.replaceChild(style, owner);
      } else {
        document.head.appendChild(style);
      }
    } catch {
      // Cross-origin CSSOM remains as its original link/style node.
    }
  }

  document.querySelectorAll('style').forEach((element: any) => {
    if (
      element.textContent?.includes('createHotContext') ||
      element.textContent?.includes('import.meta.hot')
    ) {
      element.remove();
    }
  });
  document.querySelectorAll('link[rel="preload"][as="font"]').forEach((element: any) =>
    element.remove(),
  );

  return totalRules;
}
