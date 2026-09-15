# Codex Director

![Codex × Director — Turn scripts into a cinematic plan](assets/director-hero.png)

> Turn selected screenplay scenes into directorial intent, audiovisual style, blocking, shot intent, and an executable production route.

[English](README.md) | [简体中文](README.zh-CN.md)

## Status and version

**Design and implementation-planning baseline only. The plugin is not implemented, packaged, or installed.** This repository intentionally contains no empty Skill or MCP manifest that a host could mistake for a working plugin.

The planned plugin ID is `codex-director`; the repository is `codex-director-plugin`.

## Inputs and outputs

- Inputs: selected Screenplay / Scene revision, StoryBible, asset specifications, target aspect ratio and duration, and execution policy.
- Outputs: DirectorPlan, SceneTreatment, ShotIntent, ContinuityConstraints, ProductionRoute, and ChangeProposal.

## Boundaries

The Director explains how to film without silently changing what happens or what characters say. Shot intent remains distinct from the final Shot / Panel, so this plugin does not duplicate Storyboard data.

Creative work runs in the Codex / WorkBuddy host and is saved through the workbench MCP as a reviewable version. This plugin owns no independent database. Codex packaging and WorkBuddy integration are verified separately; compatibility between the two is not assumed.

## Documentation

- [Plugin specification](docs/superpowers/specs/plugin-design.md)
- [Implementation plan](docs/superpowers/plans/implementation.md)
- [Workbench architecture](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/architecture.md)
- [Shared contracts](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/contracts.md)
- [End-to-end workflows](https://github.com/partme-ai/creative-production-workbench/blob/main/docs/superpowers/specs/workflows.md)

## License

This repository currently contains original project design documents, is private, and has no selected open-source license.
