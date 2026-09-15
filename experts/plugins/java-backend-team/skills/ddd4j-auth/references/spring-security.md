# Spring Security

Entry points: SecuritySubject, SecuritySubjectProvider, AuthUserDetails, SecurityExceptionHandler.

- Map AuthPrincipal from the SecurityContextHolder Authentication.
- Distinguish unauthenticated, anonymous, and authenticated.
- The GrantedAuthority-to-role/permission mapping must be explicit.
- The Security filter chain cleans up at request end; async propagation needs separate configuration.
- OAuth2/OIDC is Spring Security configuration and does not automatically mean the ddd4j Subject is registered.
