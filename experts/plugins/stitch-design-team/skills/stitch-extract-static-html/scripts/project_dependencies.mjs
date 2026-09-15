import { createRequire } from 'node:module';
import path from 'node:path';

// A synthetic filename anchors both preflight and runtime at the authorized cwd.
export function projectRequire(cwd = process.cwd()) {
  return createRequire(path.join(path.resolve(cwd), '__stitch_dependency_context__.cjs'));
}

export function requireProjectDependency(name, cwd = process.cwd()) {
  try {
    return projectRequire(cwd)(name);
  } catch {
    throw new ProjectDependencyError(name);
  }
}

export class ProjectDependencyError extends Error {
  constructor(name) {
    super(`Missing or incompatible target project dependency: ${name}. Run from the authorized application directory and ask its owner to install or repair this package. Nothing was installed.`);
    this.name = 'ProjectDependencyError';
  }
}
