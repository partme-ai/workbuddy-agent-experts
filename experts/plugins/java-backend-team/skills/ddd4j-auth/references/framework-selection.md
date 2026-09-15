# Framework Selection

| Dimension | Sa-Token | Shiro | Spring Security |
|---|---|---|---|
| Current module | ddd4j-auth-satoken | ddd4j-auth-shiro | ddd4j-auth-security |
| Unified exit | SaTokenSubjectProvider | ShiroSubjectProvider | SecuritySubjectProvider |
| Native context | StpLogic | Shiro Subject | SecurityContextHolder |
| Strengths | Multiple account types / temporary tokens | Realm/permission model | Spring/OAuth2/OIDC |
| Main risk | Mixing account systems | ThreadLocal cleanup | Filter/Context lifecycle |

Select one primary SubjectProvider; if multiple frameworks coexist, the priority must be defined explicitly.
