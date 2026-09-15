import assert from 'node:assert/strict';
import test from 'node:test';
import { EventEmitter } from 'node:events';
import { Readable } from 'node:stream';
import dns from 'node:dns/promises';
import http from 'node:http';
import https from 'node:https';
import { fetchAndEncode, jsxToHtml, buildHead, embedImages } from '../scripts/extract_inline_html.ts';
import { snapshot } from '../scripts/snapshot.ts';
import { createRequire } from 'node:module';
import path from 'node:path';
const runtimeRequire = createRequire(path.resolve(path.dirname(process.env.STITCH_TSX_CLI), '../../../package.json'));
const puppeteer = runtimeRequire('puppeteer').default;
process.chdir(path.resolve(path.dirname(process.env.STITCH_TSX_CLI), '../../..'));

// Only DNS and transport are faked: the real downloader performs validation,
// redirect handling, address selection and constructs the connection options.
function fakeNetwork(t, answers, responses = []) {
  const connections = [];
  const lookups = [];
  const originalLookup = dns.lookup;
  const originalHttp = http.get;
  const originalHttps = https.get;
  dns.lookup = async (hostname) => {
    lookups.push(hostname);
    return typeof answers === 'function' ? answers(hostname, lookups.length) : answers;
  };
  http.get = https.get = (url, options, callback) => {
    const req = new EventEmitter();
    req.destroy = () => {};
    connections.push({ url: String(url), options });
    queueMicrotask(() => {
      const response = responses.shift() ?? {};
      if (response.error) { req.emit('error', new Error(response.error)); return; }
      const stream = Readable.from([Buffer.from('offline-image')]);
      stream.statusCode = response.status ?? 200;
      stream.headers = response.headers ?? { 'content-type': 'image/png' };
      callback(stream);
    });
    return req;
  };
  t.after(() => { dns.lookup = originalLookup; http.get = originalHttp; https.get = originalHttps; });
  return { connections, lookups };
}

function captureLogs(t) {
  const output = [];
  for (const method of ['log', 'warn', 'error']) {
    const original = console[method];
    console[method] = (...args) => output.push(args.join(' '));
    t.after(() => { console[method] = original; });
  }
  return output;
}

test('F1 blocks IPv6 local and mapped literals before transport', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, []);
  for (const host of ['[::ffff:127.0.0.1]', '[::ffff:10.0.0.1]', '[fc00::1]', '[fd12::1]', '[fe80::1]', '[::]', '[ff02::1]', '100.64.0.1', '198.18.0.1']) {
    await fetchAndEncode(`http://${host}/private.png`, 1000);
  }
  assert.equal(fake.connections.length, 0, 'Non-public literals must never reach transport');
});

test('F1 rejects a DNS answer set containing any private answer', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, [{ address: '93.184.216.34', family: 4 }, { address: '10.0.0.1', family: 4 }]);
  await fetchAndEncode('https://mixed-answers.example/image.png', 1000);
  assert.equal(fake.connections.length, 0, 'A public answer must not hide another private answer');
  assert.equal(fake.lookups.length, 1);
});

test('F1 binds the actual connection to a validated answer without a second DNS query', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, (_, count) => [{ address: count === 1 ? '93.184.216.34' : '127.0.0.1', family: 4 }]);
  assert.match(await fetchAndEncode('https://rebind.example/image.png', 1000), /^data:image\/png;base64,/);
  assert.equal(fake.lookups.length, 1, 'Resolve and validate before opening the connection');
  const options = fake.connections[0].options;
  assert.equal(typeof options.lookup, 'function', 'Transport needs a pinned lookup callback');
  assert.equal(options.agent, false, 'Do not reuse a socket validated for a previous request');
  const bound = await new Promise((resolve, reject) => options.lookup('rebind.example', {}, (err, address, family) => err ? reject(err) : resolve({ address, family })));
  assert.deepEqual(bound, { address: '93.184.216.34', family: 4 });
  const all = await new Promise((resolve, reject) => options.lookup('rebind.example', { all: true }, (err, addresses) => err ? reject(err) : resolve(addresses)));
  assert.deepEqual(all, [{ address: '93.184.216.34', family: 4 }]);
  assert.equal(new URL(fake.connections[0].url).hostname, 'rebind.example', 'Keep hostname for Host and TLS verification');
  assert.notEqual(options.rejectUnauthorized, false);
  assert.equal(fake.lookups.length, 1, 'Pinned lookup must not resolve the hostname again');
});

test('F1 allows a public IPv6 address while rejecting empty DNS answers', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, []);
  assert.match(await fetchAndEncode('https://[2606:4700:4700::1111]/v6.png', 1000), /^data:image\/png;/);
  await fetchAndEncode('https://empty-answers.example/image.png', 1000);
  assert.equal(fake.connections.length, 1);
  assert.deepEqual(fake.lookups, ['empty-answers.example']);
});

test('F1 validates every redirect DNS answer before opening another connection', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, (host) => [{ address: host === 'redirect-start.example' ? '93.184.216.34' : 'fd00::1', family: host === 'redirect-start.example' ? 4 : 6 }], [{ status: 302, headers: { location: 'https://redirect-private.example/target.png' } }]);
  await fetchAndEncode('https://redirect-start.example/image.png', 1000);
  assert.equal(fake.connections.length, 1, 'Redirect to a private DNS answer must stop before transport');
  assert.deepEqual(fake.lookups, ['redirect-start.example', 'redirect-private.example']);
});

test('F2 downloader logs never include URL credentials, query, fragment, or raw errors', async (t) => {
  const output = captureLogs(t);
  fakeNetwork(t, [{ address: '93.184.216.34', family: 4 }], [{}, { error: 'untrusted error ERROR_SENTINEL' }]);
  await fetchAndEncode('https://USER_SENTINEL:PASS_SENTINEL@logs.example/image.png?sig=QUERY_SENTINEL#FRAGMENT_SENTINEL', 1000);
  await fetchAndEncode('https://logs-error.example/image.png?sig=QUERY_SENTINEL', 1000);
  await fetchAndEncode('invalid-URL-QUERY_SENTINEL', 1000);
  assert.doesNotMatch(output.join('\n'), /USER_SENTINEL|PASS_SENTINEL|QUERY_SENTINEL|FRAGMENT_SENTINEL|ERROR_SENTINEL/);
});

test('F2 snapshot protects navigation, browser console, error, and JSON diagnostics', async (t) => {
  const output = captureLogs(t);
  const originalLaunch = puppeteer.launch;
  let closed = false;
  puppeteer.launch = async () => ({
    close: async () => { closed = true; },
    newPage: async () => ({
      setViewport: async () => {},
      on: (event, callback) => { if (event === 'console') callback({ type: () => 'warning', text: () => 'PAGE_SENTINEL secret from page' }); },
      goto: async () => { throw new Error('NAV_SENTINEL https://user:PASS_SENTINEL@site.example/?secret=QUERY_SENTINEL'); },
    }),
  });
  t.after(() => { puppeteer.launch = originalLaunch; });
  await assert.rejects(snapshot({ url: 'https://USER_SENTINEL:PASS_SENTINEL@site.example/page?sig=QUERY_SENTINEL#FRAGMENT_SENTINEL', output: '/unused', viewport: '390x884', wait: 0, timeout: 1000, json: true }));
  assert.equal(closed, true);
  assert.doesNotMatch(output.join('\n'), /USER_SENTINEL|PASS_SENTINEL|QUERY_SENTINEL|FRAGMENT_SENTINEL|PAGE_SENTINEL|NAV_SENTINEL/);
  const json = output.find((entry) => entry.trim().startsWith('{'));
  assert.ok(json, 'Failure JSON must remain useful without raw exception details');
  assert.equal(JSON.parse(json).url, 'https://site.example/page');
});

test('F3 escapes JSX text, expressions, attributes, title and style boundaries', () => {
  const html = jsxToHtml(`export default function Page() { return <main title={'" onmouseover="alert(1)'} data-template={\`" onfocus="alert(2)\`} style={{ fontFamily: '" onblur="alert(3)' }}><p>&lt;img src=x onerror=alert(4)&gt; &amp; {'<script>alert(5)</script>'}{\`<img src=x>\`}</p><title>{'</title><img src=x>'}</title><style>{'a::after { content: "</style><img src=x>"; }'}</style></main>; }`);
  assert.ok(html);
  assert.doesNotMatch(html, /<img|<script|" on(?:mouseover|focus|blur)=/i);
  assert.match(html, /&lt;img src=x onerror=alert\(4\)&gt; &amp;/);
  assert.match(html, /title="&quot; onmouseover=&quot;alert\(1\)"/);
  assert.equal((html.match(/<\/style>/g) ?? []).length, 1);
  assert.equal((html.match(/<\/title>/g) ?? []).length, 1);
  const head = buildHead({ noTailwind: true, tailwindConfig: null, indexCss: null, cssFiles: [], extraCss: null, htmlClass: '" onload="alert(6)' });
  assert.doesNotMatch(head, /" onload=/);
});

test('F3 escaping preserves signed resource URLs and quoted inline CSS during embedding', async (t) => {
  captureLogs(t);
  const fake = fakeNetwork(t, [{ address: '93.184.216.34', family: 4 }]);
  const html = jsxToHtml(`export default () => <main><img src="https://assets.example/a.png?a=1&amp;b=2"/><div style={{backgroundImage: 'url("https://assets.example/b.png?a=3&b=4")'}}/></main>`);
  const embedded = await embedImages(html, 1, 1000);
  assert.deepEqual(fake.connections.map((entry) => entry.url), ['https://assets.example/a.png?a=1&b=2', 'https://assets.example/b.png?a=3&b=4']);
  assert.equal((embedded.match(/data:image\/png;base64,/g) ?? []).length, 2);
  assert.doesNotMatch(embedded, /https:\/\/assets/);
});
