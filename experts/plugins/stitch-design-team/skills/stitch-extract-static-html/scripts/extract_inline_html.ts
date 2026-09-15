#!/usr/bin/env tsx
/**
 * extract_inline_html.ts — Convert JSX/React mock files to self-contained HTML.
 *
 * Uses @babel/parser for proper JSX parsing instead of fragile regex.
 * Replaces the old extract_inline_html.py script.
 *
 * Usage:
 *   node <SKILL_DIR>/scripts/run.mjs extract \
 *     --page src/MockPage.jsx:home.html:"Home Page" \
 *     --index-css src/index.css \
 *     --extra-css index.html \
 *     --outdir .stitch
 *
 * Flags:
 *   --page            Page spec as src_file:dst_filename:title (repeatable)
 *   --tailwind-config  Path to tailwind.config.js (auto-detected if omitted)
 *   --no-tailwind     Skip Tailwind CDN injection
 *   --index-css       Path to main CSS file
 *   --css-files       Additional CSS files (repeatable)
 *   --extra-css       Path to index.html to extract <style>/<link> from
 *   --html-class      Class(es) for <html> element (e.g., "dark")
 *   --outdir          Output directory (default: .stitch)
 *   --exclude-pattern Literal string to exclude from body HTML
 *   --concurrency     Max concurrent image fetches (default: 6)
 *   --timeout         HTTP request timeout in ms (default: 15000)
 *   --json            Output machine-readable JSON stats
 */

import fs from 'node:fs';
import path from 'node:path';
import https from 'node:https';
import http from 'node:http';
import type { Node } from '@babel/types';
import { pathToFileURL } from 'node:url';
import dns from 'node:dns/promises';
import { BlockList, isIP } from 'node:net';
import { safeUrl, safeError } from './safe_diagnostics.js';
import { requireProjectDependency, ProjectDependencyError } from './project_dependencies.mjs';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Opts {
  pages: string[];
  tailwindConfig: string | null;
  noTailwind: boolean;
  indexCss: string | null;
  cssFiles: string[];
  extraCss: string | null;
  htmlClass: string | null;
  outdir: string;
  excludePattern: RegExp | null;
  concurrency: number;
  timeout: number;
  json: boolean;
}

interface CssUrlRef {
  url: string;
  fullMatch: string;
  start: number;
  end: number;
}

interface PageStats {
  src: string;
  dst: string;
  sizeBytes: number;
  imagesEmbedded: number;
}

interface AllStats {
  pages: PageStats[];
  totalImages: number;
  durationMs: number;
  warnings: string[];
}

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------
// Escape all regex metacharacters in user input so it is treated as a literal
// string match when used in new RegExp(). Prevents regex injection (ReDoS).
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function parseArgs(): Opts {
  const args = process.argv.slice(2);
  const opts: Opts = {
    pages: [],
    tailwindConfig: null,
    noTailwind: false,
    indexCss: null,
    cssFiles: [],
    extraCss: null,
    htmlClass: null,
    outdir: '.stitch',
    excludePattern: null,
    concurrency: 6,
    timeout: 15000,
    json: false,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--page': opts.pages.push(args[++i]); break;
      case '--tailwind-config': opts.tailwindConfig = args[++i]; break;
      case '--no-tailwind': opts.noTailwind = true; break;
      case '--index-css': opts.indexCss = args[++i]; break;
      case '--css-files': opts.cssFiles.push(args[++i]); break;
      case '--extra-css': opts.extraCss = args[++i]; break;
      case '--html-class': opts.htmlClass = args[++i]; break;
      case '--outdir': opts.outdir = args[++i]; break;
      case '--exclude-pattern': {
        const rawPattern = args[++i];
        // Escape metacharacters so user input is treated as a literal string
        opts.excludePattern = new RegExp(escapeRegExp(rawPattern), 'gs');
        break;
      }
      case '--concurrency': opts.concurrency = parseInt(args[++i], 10); break;
      case '--timeout': opts.timeout = parseInt(args[++i], 10); break;
      case '--json': opts.json = true; break;
      case '--help':
        console.log(`
Usage: node <SKILL_DIR>/scripts/run.mjs extract --page <spec> [options]

Options:
  --page             src_file:dst_filename:title (repeatable)
  --tailwind-config  Path to tailwind.config.js (auto-detected)
  --no-tailwind      Skip Tailwind CDN injection
  --index-css        Path to main CSS file
  --css-files        Additional CSS files (repeatable)
  --extra-css        Path to index.html for <style>/<link> extraction
  --html-class       Class for <html> element (e.g., "dark")
  --outdir           Output directory (default: .stitch)
  --exclude-pattern  Literal string to exclude from body
  --concurrency      Max concurrent image fetches (default: 6)
  --timeout          HTTP request timeout in ms (default: 15000)
  --json             Output machine-readable JSON stats
`);
        process.exit(0);
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(1);
    }
  }

  return opts;
}

// ---------------------------------------------------------------------------
// Input validation
// ---------------------------------------------------------------------------
function validateOpts(opts: Opts): void {
  const errors: string[] = [];

  if (opts.pages.length === 0) {
    errors.push('No pages specified. Use --page src:dst:title');
  }

  for (const spec of opts.pages) {
    const parts = spec.split(':');
    if (parts.length !== 3) {
      errors.push(`Invalid page spec '${spec}'. Must be src:dst:title`);
    } else {
      const [src] = parts;
      if (!fs.existsSync(src)) {
        errors.push(`Source file not found: ${src}`);
      }
    }
  }

  if (opts.indexCss && !fs.existsSync(opts.indexCss)) {
    errors.push(`CSS file not found: ${opts.indexCss}`);
  }

  for (const f of opts.cssFiles) {
    if (!fs.existsSync(f)) {
      errors.push(`CSS file not found: ${f}`);
    }
  }

  if (opts.extraCss && !fs.existsSync(opts.extraCss)) {
    errors.push(`Extra CSS file not found: ${opts.extraCss}`);
  }

  if (isNaN(opts.concurrency) || opts.concurrency < 1 || opts.concurrency > 20) {
    errors.push('--concurrency must be between 1 and 20');
  }

  if (isNaN(opts.timeout) || opts.timeout < 1000) {
    errors.push('--timeout must be at least 1000ms');
  }

  if (errors.length > 0) {
    console.error('❌ Validation errors:');
    errors.forEach((e) => console.error(`   • ${e}`));
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Concurrency limiter
// ---------------------------------------------------------------------------
function createLimiter(concurrency: number): <T>(fn: () => Promise<T>) => Promise<T> {
  let active = 0;
  const queue: Array<() => void> = [];

  return function limit<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      const run = async () => {
        active++;
        try {
          resolve(await fn());
        } catch (e) {
          reject(e);
        } finally {
          active--;
          if (queue.length > 0) queue.shift()!();
        }
      };

      if (active < concurrency) {
        run();
      } else {
        queue.push(run);
      }
    });
  };
}

// ---------------------------------------------------------------------------
// Image embedding (with concurrency, redirect-loop protection, timeouts)
// ---------------------------------------------------------------------------
const imgCache = new Map<string, string>();
const MAX_REDIRECTS = 5;

function isImageUrl(url: string): boolean {
  const skip = ['cdn.tailwindcss.com', 'fonts.googleapis.com', '.js', '.css'];
  return !skip.some((s) => url.includes(s));
}



// Fail closed for local, reserved, multicast and transition address ranges.
const nonPublic = new BlockList();
for (const [address, prefix] of [
  ['0.0.0.0', 8], ['10.0.0.0', 8], ['100.64.0.0', 10], ['127.0.0.0', 8],
  ['169.254.0.0', 16], ['172.16.0.0', 12], ['192.0.0.0', 24], ['192.0.2.0', 24],
  ['192.88.99.0', 24], ['192.168.0.0', 16], ['198.18.0.0', 15],
  ['198.51.100.0', 24], ['203.0.113.0', 24], ['224.0.0.0', 4], ['240.0.0.0', 4],
] as const) nonPublic.addSubnet(address, prefix, 'ipv4');
for (const [address, prefix] of [
  ['2001::', 23], ['2001:db8::', 32], ['2002::', 16], ['3fff::', 20],
] as const) nonPublic.addSubnet(address, prefix, 'ipv6');
const globalIPv6 = new BlockList();
globalIPv6.addSubnet('2000::', 3, 'ipv6');

function isPublicAddress(address: string): boolean {
  const family = isIP(address);
  if (family === 4) return !nonPublic.check(address, 'ipv4');
  // IPv4-mapped, ULA, link-local, NAT64 and unspecified addresses are outside 2000::/3.
  return family === 6 && globalIPv6.check(address, 'ipv6') && !nonPublic.check(address, 'ipv6');
}

const FALLBACK_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

export async function fetchAndEncode(url: string, timeout: number, redirectCount = 0): Promise<string> {
  if (imgCache.has(url)) return imgCache.get(url)!;
  if (!isImageUrl(url)) return url;
  const fail = (reason: string): string => {
    console.warn(`  WARN: ${reason} <- ${safeUrl(url)}`);
    imgCache.set(url, FALLBACK_IMAGE);
    return FALLBACK_IMAGE;
  };
  if (redirectCount >= MAX_REDIRECTS) return fail('Too many redirects');

  let parsed: URL;
  let answer: { address: string; family: number };
  try {
    parsed = new URL(url);
    if (!['https:', 'http:'].includes(parsed.protocol)) return fail('Blocked non-HTTP URL');
    const hostname = parsed.hostname.replace(/^\[|\]$/g, '');
    const literalFamily = isIP(hostname);
    const answers = literalFamily ? [{ address: hostname, family: literalFamily }] : await dns.lookup(hostname, { all: true, verbatim: true });
    if (answers.length === 0 || answers.some((item) => !isPublicAddress(item.address) || item.family !== isIP(item.address))) {
      return fail('Blocked non-public address');
    }
    answer = answers[0];
  } catch (error) {
    return fail(`URL or DNS validation failed (${safeError(error)})`);
  }

  return new Promise((resolve) => {
    const client = parsed.protocol === 'https:' ? https : http;
    const req = client.get(parsed, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; SnapshotBot/2.0)' },
      timeout,
      // Keep the original hostname for Host and TLS certificate/SNI validation.
      // Disable pooling and DNS re-resolution: only this validated answer may connect.
      agent: false,
      lookup: (_hostname, options, callback) => {
        if (options.all) callback(null, [answer]);
        else callback(null, answer.address, answer.family);
      },
    }, (resp) => {
      if (resp.statusCode! >= 300 && resp.statusCode! < 400 && resp.headers.location) {
        resp.resume();
        let redirect: string;
        try { redirect = new URL(resp.headers.location, parsed).href; }
        catch { resolve(fail('Invalid redirect')); return; }
        fetchAndEncode(redirect, timeout, redirectCount + 1).then((result) => {
          imgCache.set(url, result);
          resolve(result);
        });
        return;
      }
      if (resp.statusCode! >= 400) {
        resp.resume();
        resolve(fail(`HTTP ${resp.statusCode}`));
        return;
      }
      const chunks: Buffer[] = [];
      resp.on('data', (chunk: Buffer) => chunks.push(chunk));
      resp.on('end', () => {
        const buffer = Buffer.concat(chunks);
        // An upstream Content-Type must not inject HTML attributes into the data URI.
        const rawType = resp.headers['content-type']?.split(';')[0].trim();
        const contentType = rawType && /^image\/[a-z0-9.+-]+$/i.test(rawType) ? rawType : 'image/jpeg';
        const result = `data:${contentType};base64,${buffer.toString('base64')}`;
        imgCache.set(url, result);
        console.log(`  Embedded ${buffer.length} bytes <- ${safeUrl(url)}`);
        resolve(result);
      });
      resp.on('error', (error: Error) => resolve(fail(`Stream error (${safeError(error)})`)));
    });
    req.on('error', (error: Error) => resolve(fail(`Request failed (${safeError(error)})`)));
    req.on('timeout', () => { req.destroy(); resolve(fail('Request timed out')); });
  });
}

// ---------------------------------------------------------------------------
// Robust CSS url() parser — character-by-character (no regex)
// ---------------------------------------------------------------------------
function extractCssUrls(text: string): CssUrlRef[] {
  const results: CssUrlRef[] = [];
  let i = 0;
  const len = text.length;

  while (i < len) {
    // Look for 'url(' — case insensitive
    if (
      i + 3 < len &&
      text[i].toLowerCase() === 'u' &&
      text[i + 1].toLowerCase() === 'r' &&
      text[i + 2].toLowerCase() === 'l' &&
      text[i + 3] === '('
    ) {
      const urlStart = i;
      i += 4;

      // Skip whitespace
      while (i < len && (text[i] === ' ' || text[i] === '\t' || text[i] === '\n' || text[i] === '\r')) i++;

      // Check for quote
      let quote: string | null = null;
      if (i < len && (text[i] === '"' || text[i] === "'")) {
        quote = text[i];
        i++;
      }

      // Read the URL value
      let url = '';
      if (quote) {
        while (i < len && text[i] !== quote) {
          if (text[i] === '\\' && i + 1 < len) {
            i++;
            url += text[i];
          } else {
            url += text[i];
          }
          i++;
        }
        if (i < len) i++; // closing quote
      } else {
        while (i < len && text[i] !== ')' && text[i] !== ' ' && text[i] !== '\t' && text[i] !== '\n') {
          url += text[i];
          i++;
        }
      }

      // Skip trailing whitespace before ')'
      while (i < len && (text[i] === ' ' || text[i] === '\t' || text[i] === '\n' || text[i] === '\r')) i++;

      if (i < len && text[i] === ')') {
        const fullMatch = text.substring(urlStart, i + 1);
        results.push({ url: url.trim(), fullMatch, start: urlStart, end: i + 1 });
        i++;
      } else {
        i = urlStart + 1;
      }
    } else {
      i++;
    }
  }

  return results;
}

/**
 * Replace CSS url() references using pre-computed positions.
 * Replaces from end-to-start to preserve earlier indices.
 */
function replaceCssUrlsInText(
  text: string,
  replacements: Array<{ start: number; end: number; dataUri: string }>,
): string {
  const sorted = [...replacements].sort((a, b) => b.start - a.start);
  for (const r of sorted) {
    text = text.substring(0, r.start) + "url('" + r.dataUri + "')" + text.substring(r.end);
  }
  return text;
}

// ---------------------------------------------------------------------------
// Image & CSS url() embedding with concurrency
// ---------------------------------------------------------------------------
function decodeAttribute(value: string): string {
  // Decode the exact entities emitted by escapeAttribute, once only.
  const entities: Record<string, string> = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'" };
  return value.replace(/&(?:amp|lt|gt|quot|#39);/g, (entity) => entities[entity]);
}

export async function embedImages(html: string, concurrency: number, timeout: number): Promise<string> {
  const limit = createLimiter(concurrency);
  const attributes = [...html.matchAll(/\b(src|poster)="(https?:\/\/[^"]+)"/g)];
  await Promise.all(attributes.map((match) => limit(async () => {
    const url = decodeAttribute(match[2]);
    await fetchAndEncode(url, timeout);
  })));
  for (const match of attributes) {
    const url = decodeAttribute(match[2]);
    const encoded = imgCache.get(url);
    if (encoded && encoded !== url) html = html.replace(match[0], match[1] + '="' + escapeAttribute(encoded) + '"');
  }

  const embedCss = async (css: string): Promise<string> => {
    const refs = extractCssUrls(css).filter((ref) => /^https?:\/\//.test(ref.url) && isImageUrl(ref.url));
    await Promise.all(refs.map((ref) => limit(() => fetchAndEncode(ref.url, timeout))));
    const replacements = refs.flatMap((ref) => {
      const encoded = imgCache.get(ref.url);
      return encoded && encoded !== ref.url ? [{ start: ref.start, end: ref.end, dataUri: encoded }] : [];
    });
    return replaceCssUrlsInText(css, replacements);
  };
  // CSS in a style element is raw text; CSS in an HTML attribute is entity-encoded.
  for (const match of [...html.matchAll(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/gi)]) {
    const replacement = match[1] + await embedCss(match[2]) + match[3];
    html = html.replace(match[0], () => replacement);
  }
  for (const match of [...html.matchAll(/\bstyle="([^"]*)"/g)]) {
    const replacement = 'style="' + escapeAttribute(await embedCss(decodeAttribute(match[1]))) + '"';
    html = html.replace(match[0], () => replacement);
  }
  return html;
}

// ---------------------------------------------------------------------------
// JSX → HTML conversion using Babel AST
// ---------------------------------------------------------------------------

// Convert camelCase to kebab-case
function camelToKebab(str: string): string {
  return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
}

// SVG attribute mapping
const SVG_ATTRS: Record<string, string> = {
  strokeLinecap: 'stroke-linecap', strokeLinejoin: 'stroke-linejoin',
  strokeWidth: 'stroke-width', strokeDasharray: 'stroke-dasharray',
  strokeDashoffset: 'stroke-dashoffset', strokeMiterlimit: 'stroke-miterlimit',
  strokeOpacity: 'stroke-opacity', stopColor: 'stop-color',
  stopOpacity: 'stop-opacity', fillRule: 'fill-rule', fillOpacity: 'fill-opacity',
  clipRule: 'clip-rule', clipPath: 'clip-path', viewBox: 'viewBox',
  xlinkHref: 'xlink:href', xmlSpace: 'xml:space', xmlLang: 'xml:lang',
};

// React attribute mapping
const REACT_ATTRS: Record<string, string> = {
  className: 'class', htmlFor: 'for', defaultValue: 'value',
  defaultChecked: 'checked', tabIndex: 'tabindex', autoFocus: 'autofocus',
  autoComplete: 'autocomplete', crossOrigin: 'crossorigin',
};

// HTML void elements (self-closing)
const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

export function jsxToHtml(jsxSource: string): string | null {
  const parser = requireProjectDependency('@babel/parser') as typeof import('@babel/parser');
  const traverse = (requireProjectDependency('@babel/traverse') as typeof import('@babel/traverse')).default;
  let ast;
  try {
    ast = parser.parse(jsxSource, {
      sourceType: 'module',
      // Standard optional chaining and nullish coalescing no longer need plugins.
      plugins: ['jsx', 'typescript'],
    });
  } catch (e: unknown) {
    console.error(`  Babel parse error: ${safeError(e)}`);
    return null;
  }

  // Strategy 1: Prefer the JSX return inside the default-exported function,
  // since that's the main component in the vast majority of React files.
  let returnedJSX: Node | null = null;

  traverse(ast, {
    ExportDefaultDeclaration(path) {
      const decl = path.node.declaration;

      // Handle: export default function Component() { return <JSX/> }
      if (decl.type === 'FunctionDeclaration') {
        path.traverse({
          ReturnStatement(retPath) {
            const arg = retPath.node.argument;
            if (arg && (arg.type === 'JSXElement' || arg.type === 'JSXFragment')) {
              returnedJSX = arg;
              retPath.stop();
            }
          },
        });
        if (returnedJSX) path.stop();
      }

      // Handle: export default () => <JSX/> or export default () => { return <JSX/> }
      if (decl.type === 'ArrowFunctionExpression') {
        if (decl.body.type === 'JSXElement' || decl.body.type === 'JSXFragment') {
          returnedJSX = decl.body;
          path.stop();
        } else {
          path.traverse({
            ReturnStatement(retPath) {
              const arg = retPath.node.argument;
              if (arg && (arg.type === 'JSXElement' || arg.type === 'JSXFragment')) {
                returnedJSX = arg;
                retPath.stop();
              }
            },
          });
          if (returnedJSX) path.stop();
        }
      }
    },
  });

  // Strategy 2: Fallback — find the return with the largest JSX tree.
  // Covers files that use `export default ComponentName` (identifier) at the
  // bottom, or files without any default export at all.
  if (!returnedJSX) {
    let maxLen = -1;
    traverse(ast, {
      ReturnStatement(path) {
        const arg = path.node.argument;
        if (arg && (arg.type === 'JSXElement' || arg.type === 'JSXFragment')) {
          const len = (arg.end || 0) - (arg.start || 0);
          if (len > maxLen) {
            maxLen = len;
            returnedJSX = arg;
          }
        }
      },
    });
  }

  if (!returnedJSX) {
    console.error('  No JSX return statement found');
    return null;
  }

  return renderNode(returnedJSX);
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeAttribute(value: string): string {
  return escapeHtml(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function escapeStyle(value: string): string {
  // <style> is raw text: HTML entities would change CSS; use a CSS escape.
  return value.replace(/</g, '\\3c ');
}

function renderNode(node: any): string {
  if (!node) return '';

  switch (node.type) {
    case 'JSXElement':
      return renderElement(node);
    case 'JSXFragment':
      return node.children.map(renderNode).join('');
    case 'JSXText':
      return escapeHtml(node.value);
    case 'JSXExpressionContainer':
      return renderExpression(node.expression);
    case 'StringLiteral':
      return escapeHtml(node.value);
    default:
      return '';
  }
}

function renderExpression(expr: any): string {
  if (!expr) return '';
  switch (expr.type) {
    case 'JSXEmptyExpression':
      return '';
    case 'StringLiteral':
      return escapeHtml(expr.value);
    case 'NumericLiteral':
      return String(expr.value);
    case 'TemplateLiteral':
      // Flatten template literals — just join the quasis
      return escapeHtml(expr.quasis.map((q: any) => q.value.cooked ?? q.value.raw).join(''));
    default:
      console.warn(`  WARN: Unhandled JSX expression of type "${expr.type}" inside child node.`);
      return '';
  }
}

function renderElement(node: any): string {
  const tagName = getTagName(node.openingElement);
  if (tagName === 'style') {
    const css = node.children.map((child: any) => {
      if (child.type === 'JSXText') return child.value;
      const expression = child.expression;
      if (expression?.type === 'StringLiteral') return expression.value;
      if (expression?.type === 'TemplateLiteral') return expression.quasis.map((q: any) => q.value.cooked ?? q.value.raw).join('');
      return '';
    }).join('');
    return `<style${renderAttributes(node.openingElement.attributes, tagName)}>${escapeStyle(css)}</style>`;
  }

  // Skip <Link> — render children in a <div>
  if (tagName === 'Link') {
    const attrs = renderAttributes(node.openingElement.attributes, 'div');
    const children = node.children.map(renderNode).join('');
    return `<div${attrs}>${children}</div>`;
  }

  // Skip unknown components (capitalized) — just render children
  if (tagName[0] === tagName[0].toUpperCase() && tagName[0] !== tagName[0].toLowerCase()) {
    return node.children.map(renderNode).join('');
  }

  const attrs = renderAttributes(node.openingElement.attributes, tagName);
  const selfClosing = node.openingElement.selfClosing;

  if (selfClosing && VOID_ELEMENTS.has(tagName)) {
    return `<${tagName}${attrs}/>`;
  }

  const children = node.children.map(renderNode).join('');

  if (selfClosing && !VOID_ELEMENTS.has(tagName)) {
    return `<${tagName}${attrs}></${tagName}>`;
  }

  return `<${tagName}${attrs}>${children}</${tagName}>`;
}

function getTagName(openingElement: any): string {
  if (openingElement.name.type === 'JSXIdentifier') {
    return openingElement.name.name;
  }
  if (openingElement.name.type === 'JSXMemberExpression') {
    return `${openingElement.name.object.name}.${openingElement.name.property.name}`;
  }
  return 'div';
}

function renderAttributes(attrs: any[], tagName: string): string {
  if (!attrs || attrs.length === 0) return '';

  const parts: string[] = [];
  for (const attr of attrs) {
    if (attr.type === 'JSXSpreadAttribute') continue; // Skip {...props}

    let name: string = attr.name?.name || '';

    // Skip event handlers and React-specific props
    if (/^on/i.test(name)) continue;
    if (['key', 'ref', 'dangerouslySetInnerHTML'].includes(name)) continue;

    // Map React attributes
    if (REACT_ATTRS[name]) name = REACT_ATTRS[name];
    else if (SVG_ATTRS[name]) name = SVG_ATTRS[name];

    // Handle value
    if (!attr.value) {
      // Boolean attribute like `checked`
      parts.push(name);
      continue;
    }

    if (attr.value.type === 'StringLiteral') {
      // Skip `to` attribute from Link (already handled)
      if (name === 'to') continue;
      parts.push(`${name}="${escapeAttribute(attr.value.value)}"`);
    } else if (attr.value.type === 'JSXExpressionContainer') {
      const expr = attr.value.expression;
      if (name === 'style' && expr.type === 'ObjectExpression') {
        // Convert style={{...}} to style="..."
        const styleStr = renderStyleObject(expr);
        if (styleStr) parts.push(`style="${escapeAttribute(styleStr)}"`);
      } else if (expr.type === 'StringLiteral') {
        parts.push(`${name}="${escapeAttribute(expr.value)}"`);
      } else if (expr.type === 'NumericLiteral') {
        parts.push(`${name}="${expr.value}"`);
      } else if (expr.type === 'TemplateLiteral') {
        const val = expr.quasis.map((q: any) => q.value.cooked ?? q.value.raw).join('');
        parts.push(`${name}="${escapeAttribute(val)}"`);
      } else {
        console.warn(`  WARN: Unhandled JSX expression of type "${expr.type}" inside attribute "${name}".`);
      }
    }
  }

  return parts.length > 0 ? ' ' + parts.join(' ') : '';
}

function renderStyleObject(objExpr: any): string {
  const pairs: string[] = [];
  for (const prop of objExpr.properties) {
    if (prop.type !== 'ObjectProperty') continue;
    const key = prop.key.name || prop.key.value;
    if (!key) continue;
    const cssKey = camelToKebab(key);

    let val: string | undefined;
    if (prop.value.type === 'StringLiteral') val = prop.value.value;
    else if (prop.value.type === 'NumericLiteral') val = prop.value.value === 0 ? '0' : `${prop.value.value}px`;
    else if (prop.value.type === 'TemplateLiteral') val = prop.value.quasis.map((q: any) => q.value.raw).join('');
    else continue;

    pairs.push(`${cssKey}: ${val}`);
  }
  return pairs.join('; ');
}

// ---------------------------------------------------------------------------
// Tailwind & CSS helpers
// ---------------------------------------------------------------------------

function autoDetectTailwind(dir = '.'): string | null {
  for (const name of ['tailwind.config.js', 'tailwind.config.ts', 'tailwind.config.mjs', 'tailwind.config.cjs']) {
    const p = path.join(dir, name);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function readCssFile(filePath: string | null): { imports: string[]; css: string; hasApply: boolean } {
  if (!filePath || !fs.existsSync(filePath)) return { imports: [], css: '', hasApply: false };
  const content = fs.readFileSync(filePath, 'utf-8');
  const imports: string[] = [];
  const cssLines: string[] = [];
  for (const line of content.split('\n')) {
    if (line.trim().startsWith('@import')) imports.push(line.trim());
    else if (!line.trim().startsWith('@tailwind')) cssLines.push(line);
  }
  const css = cssLines.join('\n');
  return { imports, css, hasApply: /@apply\s+/.test(css) };
}

function extractFromHtml(htmlPath: string | null): { styles: string; links: string[] } {
  if (!htmlPath || !fs.existsSync(htmlPath)) return { styles: '', links: [] };
  const html = fs.readFileSync(htmlPath, 'utf-8');
  const styles: string[] = [];
  const links: string[] = [];
  // Extract <style> blocks
  for (const m of html.matchAll(/<style[^>]*>(.*?)<\/style>/gs)) {
    styles.push(m[1].trim());
  }
  // Extract stylesheet <link> tags with http URLs
  for (const m of html.matchAll(/<link[^>]+href="([^"]+)"[^>]*rel="stylesheet"[^>]*\/?>|<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"[^>]*\/?>/g)) {
    const href = m[1] || m[2];
    if (href?.startsWith('http')) links.push(href);
  }
  return { styles: styles.join('\n'), links };
}

// ---------------------------------------------------------------------------
// Robust @import URL extraction using parser (not regex)
// ---------------------------------------------------------------------------
function extractImportUrl(importLine: string): string | null {
  // Handle: @import url("..."), @import url('...'), @import url(...)
  const urlRefs = extractCssUrls(importLine);
  if (urlRefs.length > 0) return urlRefs[0].url;

  // Handle: @import "..." and @import '...'
  const quoteMatch = importLine.match(/@import\s+['"]([^'"]+)['"]/);
  if (quoteMatch) return quoteMatch[1];

  return null;
}

// ---------------------------------------------------------------------------
// Build head template
// ---------------------------------------------------------------------------
export function buildHead(opts: Opts): string {
  let useTailwind = !opts.noTailwind;
  let tailwindConfig = opts.tailwindConfig;

  if (useTailwind && !tailwindConfig) {
    tailwindConfig = autoDetectTailwind();
    if (tailwindConfig) console.log(`Auto-detected Tailwind config: ${tailwindConfig}`);
    else { useTailwind = false; console.log('No Tailwind config found — skipping CDN.'); }
  }

  // Read CSS
  const indexCss = readCssFile(opts.indexCss);
  let hasApply = indexCss.hasApply;

  let extraCssContent = '';
  for (const f of opts.cssFiles) {
    if (fs.existsSync(f)) {
      const content = fs.readFileSync(f, 'utf-8');
      extraCssContent += `/* --- ${path.basename(f)} --- */\n${content}\n`;
      if (/@apply\s+/.test(content)) hasApply = true;
      console.log(`Included CSS: ${f}`);
    }
  }

  const htmlExtra = extractFromHtml(opts.extraCss);

  // Build head
  const htmlAttrs = opts.htmlClass ? ` lang="en" class="${escapeAttribute(opts.htmlClass)}"` : ' lang="en"';
  let head = `<!DOCTYPE html>\n<html${htmlAttrs}><head>\n<meta charset="utf-8"/>\n<meta content="width=device-width, initial-scale=1.0" name="viewport"/>\n`;

  if (useTailwind) {
    head += '<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>\n';
  }

  // @import → <link> (using robust parser)
  for (const imp of indexCss.imports) {
    const href = extractImportUrl(imp);
    if (href) head += `<link href="${escapeAttribute(href)}" rel="stylesheet"/>\n`;
  }

  // Extra font links from index.html
  for (const href of htmlExtra.links) {
    head += `<link href="${escapeAttribute(href)}" rel="stylesheet"/>\n`;
  }

  // Tailwind config
  if (useTailwind && tailwindConfig && fs.existsSync(tailwindConfig)) {
    let tw = fs.readFileSync(tailwindConfig, 'utf-8');
    tw = tw.replace(/export\s+default\s+/, 'tailwind.config = ');
    tw = tw.replace(/module\.exports\s*=\s*/, 'tailwind.config = ');
    tw = tw.replace(/.*require\(['"]tailwindcss\/colors['"]\).*\n?/g, '');
    head += `<script>\n${tw}\n</script>\n`;
  }

  // Combined CSS
  const allCss = `body {\n  min-height: 100dvh;\n}\n${indexCss.css}\n${extraCssContent}\n${htmlExtra.styles}`;
  const styleType = hasApply && useTailwind ? ' type="text/tailwindcss"' : '';
  if (hasApply && useTailwind) {
    console.log('Detected @apply — using <style type="text/tailwindcss">');
  }
  head += `<style${styleType}>\n${escapeStyle(allCss)}</style>\n</head>\n`;

  return head;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main(): Promise<void> {
  const opts = parseArgs();
  validateOpts(opts);

  const startTime = Date.now();
  const head = buildHead(opts);
  const stats: AllStats = {
    pages: [],
    totalImages: 0,
    durationMs: 0,
    warnings: [],
  };

  fs.mkdirSync(opts.outdir, { recursive: true });

  for (const spec of opts.pages) {
    const parts = spec.split(':');
    const [src, dstName, title] = parts;
    const dst = path.join(opts.outdir, dstName);

    console.log(`\n${'='.repeat(60)}`);
    console.log(`Converting ${src} -> ${dstName}...`);
    console.log(`${'='.repeat(60)}`);

    const jsx = fs.readFileSync(src, 'utf-8');
    let body = jsxToHtml(jsx);

    if (!body) {
      const msg = `Failed to parse JSX from ${src}`;
      console.error(`  ${msg}`);
      stats.warnings.push(msg);
      continue;
    }

    // Apply exclude pattern (pre-validated during argument parsing)
    if (opts.excludePattern) {
      body = body.replace(opts.excludePattern, '');
    }

    // Extract body class from outer wrapper div
    const outerMatch = body.match(/^<div\s+class="([^"]*)"[^>]*>([\s\S]*)<\/div>$/);
    let fullHtml: string;
    if (outerMatch) {
      fullHtml = head.replace('</head>', () => `<title>${escapeHtml(title)}</title></head>`) +
        `<body class="${outerMatch[1]}">\n${outerMatch[2].trim()}\n</body></html>\n`;
    } else {
      fullHtml = head.replace('</head>', () => `<title>${escapeHtml(title)}</title></head>`) +
        `<body>\n${body}\n</body></html>\n`;
    }

    // Embed remote images with concurrency
    const cacheCountBefore = imgCache.size;
    fullHtml = await embedImages(fullHtml, opts.concurrency, opts.timeout);
    const imagesEmbedded = imgCache.size - cacheCountBefore;

    fs.writeFileSync(dst, fullHtml, 'utf-8');
    const fileSize = fs.statSync(dst).size;
    console.log(`=> ${dst} (${fileSize.toLocaleString()} bytes)`);

    stats.pages.push({
      src,
      dst,
      sizeBytes: fileSize,
      imagesEmbedded,
    });
  }

  stats.totalImages = imgCache.size;
  stats.durationMs = Date.now() - startTime;

  console.log(
    `\nDONE: ${imgCache.size} unique images embedded in ${stats.durationMs}ms.`,
  );

  if (opts.json) {
    console.log('\n--- JSON Stats ---');
    console.log(JSON.stringify(stats, null, 2));
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) main().catch((err: Error) => {
  console.error('❌ Error:', err instanceof ProjectDependencyError ? err.message : safeError(err));
  process.exit(1);
});
