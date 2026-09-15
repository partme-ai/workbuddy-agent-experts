# Applicability Matrix

Select optional sections before drafting. Keep detailed examples available, but include them in the delivered document only when the target architecture or business model requires them.

| Capability | Include when | Otherwise |
|---|---|---|
| Open-source/commercial dual track | The product has two maintained distributions | Remove dual-track naming, pricing, and feature-wall sections |
| SaaS multi-tenancy | Multiple organizations share a hosted control plane | Replace with single-tenant or on-premises boundaries |
| DDD/COLA | Domain complexity and team structure justify explicit domain boundaries | Use the project's actual layered, modular, hexagonal, or simpler architecture |
| CQRS/event-driven | Read/write separation or asynchronous workflows are real requirements | Keep synchronous request/response examples |
| Agent orchestration | The product coordinates models, agents, tools, or workflows | Replace Agent-specific terms with target domain concepts |
| CLI/IM channels | Users operate through command line or messaging channels | Remove those menu and adapter sections |
| Mobile application | Mobile delivery is in scope | Remove mobile compatibility, app distribution, and mobile interaction sections |
| Enterprise governance | RBAC, audit, compliance, and private deployment are contracted requirements | Keep only the security controls supported by evidence |

Record each decision as `启用`, `不适用`, or `待确认`. Never infer a complex architecture solely because the template contains a complete example.
