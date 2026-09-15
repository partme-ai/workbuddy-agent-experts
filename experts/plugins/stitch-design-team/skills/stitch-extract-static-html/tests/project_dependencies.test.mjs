import assert from 'node:assert/strict';
import test from 'node:test';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const runtime = process.env.STITCH_TSX_CLI;
const project = runtime ? path.resolve(path.dirname(runtime), '../../..') : '';
const scripts = fileURLToPath(new URL('../scripts/', import.meta.url));
for (const script of ['snapshot.ts', 'extract_inline_html.ts']) {
  test(`F4 ${script} uses the target project dependencies without tsconfig aliases`, { skip: !runtime }, () => {
    const input = fs.mkdtempSync(path.join(os.tmpdir(), 'stitch-deps-'));
    try {
      fs.writeFileSync(path.join(input, 'Page.jsx'), 'export default () => <main>project-runtime</main>');
      const args = script === 'snapshot.ts' ? ['snapshot', '--check'] : ['extract', '--no-tailwind', '--page', `${input}/Page.jsx:page.html:Example`, '--outdir', input];
      const result = spawnSync(process.execPath, [path.join(scripts, 'run.mjs'), ...args], { cwd: project, env: { ...process.env, TSX_TSCONFIG_PATH: '' }, encoding: 'utf8', timeout: 30000 });
      assert.equal(result.status, 0, result.stderr);
      if (script !== 'snapshot.ts') assert.match(fs.readFileSync(path.join(input, 'page.html'), 'utf8'), /<main>project-runtime<\/main>/);
    } finally { fs.rmSync(input, { force: true, recursive: true }); }
  });
}

test('F4 missing target dependencies fail with actionable instructions and create no packages', { skip: !runtime }, () => {
  const projectWithoutPackages = fs.mkdtempSync(path.join(os.tmpdir(), 'stitch-no-deps-'));
  try {
    const result = spawnSync(process.execPath, [runtime, path.join(scripts, 'snapshot.ts'), '--url', 'http://localhost:5173', '--output', 'out.html'], { cwd: projectWithoutPackages, env: { ...process.env, TSX_TSCONFIG_PATH: '' }, encoding: 'utf8', timeout: 30000 });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /target project|目标项目/i);
    assert.match(result.stderr, /puppeteer/);
    assert.match(result.stderr, /install|安装/i);
    const preflight = spawnSync(process.execPath, [path.join(scripts, 'run.mjs'), 'snapshot', '--check'], { cwd: projectWithoutPackages, encoding: 'utf8', timeout: 30000 });
    assert.notEqual(preflight.status, 0);
    assert.match(preflight.stderr, /target project dependency: tsx/);
    assert.match(preflight.stderr, /Nothing was installed/);
    assert.deepEqual(fs.readdirSync(projectWithoutPackages), []);
  } finally { fs.rmSync(projectWithoutPackages, { force: true, recursive: true }); }
});
