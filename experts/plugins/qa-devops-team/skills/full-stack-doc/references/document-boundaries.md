# Document Boundaries

## Product-level documents

Define facts that apply across versions: brand, terminology, market, technical feasibility, architecture direction, product roadmap, domain model, visual DNA, and global navigation.

Do not place version-specific API contracts, temporary implementation details, or module acceptance cases here unless marked as examples.

The complete [`architecture/架构设计文档模板.md`](../templates/architecture/架构设计文档模板.md) is a source library for a standalone system/component architecture or for enriching the product baseline. Product document `root/8、系统架构设计.md` should keep only cross-version architecture contracts and link component, protocol, deployment, and runbook details rather than copying the entire standalone template.

## Version-level documents

Define one release: research evidence, requirements, version architecture delta, page/module plan, version PRD, version menu scope, and version-wide UI rules.

- Version PRD owns goals, scope, cross-module journeys, shared rules, non-functional requirements, and release acceptance.
- Version architecture owns changes from the product architecture baseline, not a duplicate of the entire root architecture.
- Version architecture may borrow migration, compatibility, deployment, risk, and acceptance sections from the complete architecture template, but records only the release delta.
- Version UI owns navigation, layout, global components, design tokens, and cross-page behavior.

## Module-level documents

Define one bounded functional area.

- Module PRD owns module states, detailed rules, APIs, errors, permissions, analytics, and module acceptance.
- Module design prompt owns target pages, data states, design constraints, and generation instructions.
- Module UI owns page anatomy, component states, local interactions, responsive behavior, and implementation review.

Do not duplicate the complete version PRD or version UI specification. Link to shared rules and describe only module-specific deltas.

## Delivery documents

Record the evidence needed to hand work across development, testing, release, and operations. Delivery documents must link to current filenames, avoid live secrets, and distinguish examples from actual environment data.
