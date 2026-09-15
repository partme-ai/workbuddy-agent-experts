import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('../scripts/post_process.ts', import.meta.url));

function runPostProcess(html, resourceRoot) {
  const result = spawnSync(
    process.execPath,
    ['--experimental-strip-types', script, html, '--base-dir', resourceRoot],
    { encoding: 'utf8' },
  );
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return fs.readFileSync(html, 'utf8');
}

test('rejects absolute, parent, and symlink paths outside the resource root', () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'stitch-post-process-'));
  const resourceRoot = path.join(fixture, 'assets');
  const outside = path.join(fixture, 'outside.png');
  const html = path.join(fixture, 'page.html');
  fs.mkdirSync(resourceRoot);
  fs.writeFileSync(outside, 'not-a-real-png');
  fs.symlinkSync(outside, path.join(resourceRoot, 'linked.png'));

  const input = [
    `<img src="${outside}">`,
    '<img src="../outside.png">',
    '<img src="linked.png">',
  ].join('\n');
  fs.writeFileSync(html, input);

  assert.equal(runPostProcess(html, resourceRoot), input);
});

test('does not inline files with an unsupported extension', () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'stitch-post-process-'));
  const resourceRoot = path.join(fixture, 'assets');
  const html = path.join(fixture, 'page.html');
  fs.mkdirSync(resourceRoot);
  fs.writeFileSync(path.join(resourceRoot, 'secret.txt'), 'do not inline');
  const input = '<img src="secret.txt">';
  fs.writeFileSync(html, input);

  assert.equal(runPostProcess(html, resourceRoot), input);
});
