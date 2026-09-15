#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { projectRequire, requireProjectDependency, ProjectDependencyError } from './project_dependencies.mjs';

const [mode, ...args] = process.argv.slice(2);
const dependencies = {
  snapshot: ['puppeteer'],
  extract: ['@babel/parser', '@babel/traverse'],
  'post-process': [],
};
const files = { snapshot: 'snapshot.ts', extract: 'extract_inline_html.ts', 'post-process': 'post_process.ts' };
if (!Object.hasOwn(dependencies, mode ?? '')) {
  console.error('Usage: node <SKILL_DIR>/scripts/run.mjs snapshot|extract|post-process [--check | script options]');
  process.exit(1);
}
try {
  const project = projectRequire();
  let runtime;
  try { runtime = project.resolve('tsx/cli'); } catch { throw new ProjectDependencyError('tsx'); }
  for (const dependency of dependencies[mode]) requireProjectDependency(dependency);
  if (args.length === 1 && args[0] === '--check') {
    console.log(`Target project dependencies ready for ${mode}; nothing installed.`);
  } else {
    const script = path.join(path.dirname(fileURLToPath(import.meta.url)), files[mode]);
    const result = spawnSync(process.execPath, [runtime, script, ...args], { cwd: process.cwd(), stdio: 'inherit' });
    process.exitCode = result.status ?? 1;
  }
} catch (error) {
  console.error(error instanceof ProjectDependencyError ? error.message : 'Target project preflight failed; nothing installed.');
  process.exitCode = 1;
}
