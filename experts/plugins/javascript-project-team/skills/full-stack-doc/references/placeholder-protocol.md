# Placeholder Protocol

## Purpose

Use machine placeholders only for values that must remain consistent across filenames and documents. Keep inline examples intact as authoring guidance.

## Global placeholders

| Placeholder | Meaning | Required | Example |
|---|---|:---:|---|
| `{{PRODUCT_NAME}}` | Product or brand name | Yes | `ExampleCommerce` |
| `{{OPEN_SOURCE_NAME}}` | Open-source variant | No | `ExampleCommerce-Open` |
| `{{VERSION}}` | Version directory/name | For version docs | `V1` |
| `{{MODULE_NAME}}` | Module display name | For module docs | `订单中心` |
| `{{MODULE_INDEX}}` | Module sequence number | For module directories | `1` |
| `{{DATE}}` | Document date in ISO format | Yes | `2026-07-21` |
| `{{DATETIME}}` | Date and time with timezone when relevant | No | `2026-07-21 10:00 +08:00` |
| `{{OWNER}}` | Author, reviewer, or responsible owner | Yes | `张三` |
| `{{ORGANIZATION}}` | Organization name | No | `ExampleOrg` |
| `{{DOC_ROOT}}` | Documentation root directory | Yes for generated paths | `product-docs/ExampleProduct` |

## Delivery-only placeholders

These values are resolved per environment and must never contain production secrets in the template source.

| Placeholder | Meaning |
|---|---|
| `{{TEST_BASE_URL}}` | Test environment base URL |
| `{{PREPROD_BASE_URL}}` | Pre-production base URL |
| `{{PROD_BASE_URL}}` | Production base URL |
| `{{API_BASE_URL}}` | API base URL for the named environment |
| `{{SWAGGER_URL}}` | API documentation URL |
| `{{TEST_USERNAME}}` | Non-production test account |
| `{{TEST_PASSWORD}}` | Secret-store reference or one-time test password |

## README-only placeholders

These placeholders support the project README template family. Fill them from manifests, CI, source, release metadata, and governance files rather than memory.

| Placeholder | Meaning |
|---|---|
| `{{PROJECT_NAME}}` | Public project or repository name |
| `{{PROJECT_TAGLINE}}` | One-line value proposition |
| `{{PROJECT_DESCRIPTION}}` | Short evidence-based project overview |
| `{{PACKAGE_NAME}}` | Published package, artifact, crate, image, or binary name |
| `{{CURRENT_VERSION}}` | Current documented release |
| `{{PRIMARY_LANGUAGE}}` | Primary example/source language identifier |
| `{{RUNTIME_NAME}}` | Runtime or toolchain name |
| `{{RUNTIME_VERSION}}` | Supported runtime or toolchain version |
| `{{PACKAGE_MANAGER}}` | Package/build tool command |
| `{{CONFIG_FILE}}` | Primary configuration file |
| `{{CI_BADGE_URL}}` | CI-generated badge image URL |
| `{{CI_URL}}` | CI workflow or latest run URL |
| `{{REPOSITORY_URL}}` | Public repository URL |
| `{{DOCS_URL}}` | Published or repository documentation URL |
| `{{ISSUES_URL}}` | Issue tracker URL |
| `{{LICENSE_NAME}}` | License identifier |
| `{{LICENSE_URL}}` | License file or canonical license URL |
| `{{SECURITY_CONTACT}}` | Private vulnerability reporting channel |
| `{{INSTALL_COMMAND}}` | Verified minimal installation command |
| `{{START_COMMAND}}` | Verified minimal start/example command |
| `{{BUILD_COMMAND}}` | Verified build command |
| `{{TEST_COMMAND}}` | Verified primary test command |

### Java README placeholders

| Placeholder | Meaning |
|---|---|
| `{{GROUP_ID}}` | Maven group ID |
| `{{ARTIFACT_ID}}` | Primary Maven artifact ID |
| `{{BOM_ARTIFACT_ID}}` | BOM artifact ID |
| `{{JAVA_VERSION}}` | Supported Java baseline |
| `{{MAVEN_VERSION}}` | Supported Maven baseline |
| `{{SPRING_BOOT_VERSION}}` | Supported Spring Boot line, when applicable |
| `{{CONFIG_PREFIX}}` | Verified configuration-property prefix |
| `{{MAIN_CLASS}}` | Minimal example or application main class |

### Rust README placeholders

| Placeholder | Meaning |
|---|---|
| `{{CRATE_NAME}}` | Primary published crate name |
| `{{RUST_VERSION}}` | Minimum supported Rust version (MSRV) |
| `{{RUST_EDITION}}` | Rust edition from Cargo manifests |
| `{{WORKSPACE_RESOLVER}}` | Cargo workspace resolver version |
| `{{DEFAULT_FEATURES}}` | Verified default Cargo features |

### Plugin README placeholders

| Placeholder | Meaning |
|---|---|
| `{{PLUGIN_ID}}` | Stable plugin identifier from its manifest |
| `{{HOST_NAME}}` | Host application or platform name |
| `{{HOST_VERSION}}` | Tested host version or version range |
| `{{MANIFEST_PATH}}` | Repository-relative plugin manifest path |
| `{{CONFIG_PATH}}` | Repository-relative or host-relative configuration path |

### Skill ecosystem README placeholders

| Placeholder | Meaning |
|---|---|
| `{{SKILL_COUNT}}` | Audited count of installable skills |
| `{{INSTALL_SCOPE}}` | Target ecosystem, package scope, or audience |

## Architecture output filename

The architecture template reuses `{{PROJECT_NAME}}` as the stable filename stem:

| Language | Output filename |
|---|---|
| English or default | `{{PROJECT_NAME}}-Architecture.md` |
| Simplified Chinese | `{{PROJECT_NAME}}-Architecture.zh_CN.md` |

For a component, platform, or version document, extend the stem before the fixed suffix: `{{PROJECT_NAME}}-{Component}-Architecture.zh_CN.md` or `{{PROJECT_NAME}}-{{VERSION}}-Architecture.zh_CN.md`.

Do not emit `_CN.md`, `.zh-CN.md`, lowercase `-architecture.md`, or a bare `Architecture.md`.

## Interpretation rules

1. Replace double-brace placeholders in filenames and content.
2. Treat single-brace text such as `{例如：订单中心}` as an inline example or field prompt, not as a global replacement token.
3. Do not replace braces inside code, JSON, Mermaid, regular expressions, or type definitions.
4. Remove optional sections when their applicability condition is false; do not leave unresolved global placeholders.
5. Never place real passwords, tokens, local absolute paths, or private repository names in templates.
6. Prefer a secret-store key or distribution channel for `{{TEST_PASSWORD}}`; do not commit its resolved value.

## Completion check

Before delivery, search for unresolved `{{...}}` tokens, verify that every remaining token is intentionally deferred, and confirm that examples are clearly labeled as examples rather than facts.
