# Codex Storyboard

![Codex × Storyboard — Turn direction into production-ready shots](assets/storyboard-hero.png)

> Convert an approved director plan into shot lists, visual panels, asset bindings, animatics, and production task packages.

[English](README.md) | [简体中文](README.zh-CN.md)

## Status and version

**Design and implementation-planning baseline only. The plugin is not implemented, packaged, or installed.** This repository intentionally contains no empty Skill or MCP manifest that a host could mistake for a working plugin.

The planned plugin ID is `codex-storyboard`; the repository is `codex-storyboard-plugin`.

## Inputs and outputs

- Inputs: selected Screenplay / DirectorPlan revision, ShotIntent, locked character, scene and prop versions, target duration, and asset-generation permissions.
- Outputs: ShotList, Shot / Panel, AssetBinding, AnimaticPlan, and ProductionTaskPlan / ShotExecutionPacket.

## Boundaries

The Storyboard plugin makes shots concrete without silently changing the story or locked directing decisions. Existing Image Factory and Dreamina Design plugins generate images; the workbench owns character master data.

Creative work runs in the Codex / WorkBuddy host and is saved through the workbench MCP as a reviewable version. This plugin owns no independent database. Codex packaging and WorkBuddy integration are verified separately; compatibility between the two is not assumed.

## Documentation

- [Plugin specification](docs/superpowers/specs/plugin-design.md)
- [Implementation plan](docs/superpowers/plans/implementation.md)
- [Workbench architecture](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/architecture.md)
- [Shared contracts](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/contracts.md)
- [End-to-end workflows](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/workflows.md)

## License

This repository currently contains original project design documents, is private, and has no selected open-source license.
