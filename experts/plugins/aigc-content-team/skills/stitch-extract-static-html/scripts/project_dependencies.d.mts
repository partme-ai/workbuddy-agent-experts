/** Types for the executable ESM project dependency resolver in the paired .mjs. */
export function projectRequire(cwd?: string): NodeRequire;
export function requireProjectDependency(name: string, cwd?: string): unknown;
export class ProjectDependencyError extends Error {
  constructor(name: string);
}
