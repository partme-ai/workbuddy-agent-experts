import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

// Set STITCH_TSX_CLI and optionally STITCH_TSX_TSCONFIG to an existing,
// authorized runtime with Babel dependencies. This test never installs them.
test('extracts JSX containing standard optional chaining and nullish coalescing', {
  skip: process.env.STITCH_TSX_CLI ? false : 'Requires an existing tsx/Babel runtime via STITCH_TSX_CLI',
}, () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'stitch-jsx-'));
  try {
    const input = path.join(directory, 'Page.tsx');
    const outputDirectory = path.join(directory, 'output');
    fs.writeFileSync(input, `
type Appointment = { label?: string };
const appointment: Appointment | undefined = undefined;
const label = appointment?.label ?? '演示预约';
export default function Page() {
  return <main><h1>预约列表</h1><p>暂无预约</p></main>;
}
`);
    const args = [process.env.STITCH_TSX_CLI];
    if (process.env.STITCH_TSX_TSCONFIG) args.push('--tsconfig', process.env.STITCH_TSX_TSCONFIG);
    args.push(fileURLToPath(new URL('../scripts/extract_inline_html.ts', import.meta.url)),
      '--no-tailwind', '--outdir', outputDirectory, '--page', `${input}:orders.html:$&</title><img src=x>`);
    const project = path.resolve(path.dirname(process.env.STITCH_TSX_CLI), '../../..');
    const result = spawnSync(process.execPath, args, { cwd: project, encoding: 'utf8', timeout: 30000 });
    assert.equal(result.status, 0, result.stdout + result.stderr);
    const html = fs.readFileSync(path.join(outputDirectory, 'orders.html'), 'utf8');
    assert.ok(html.includes('<main><h1>预约列表</h1><p>暂无预约</p></main>'));
    assert.ok(!html.includes('cdn.tailwindcss.com'));
    assert.ok(!result.stderr.includes('Babel parse error'));
    assert.ok(html.includes('<title>$&amp;&lt;/title&gt;&lt;img src=x&gt;</title>'));
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
