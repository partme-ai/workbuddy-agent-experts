# Apache Shiro

Entry points: ShiroSubject, ShiroSubjectProvider.

- Map principal, roles, and permissions from the current Shiro Subject.
- Return explicit anonymous/empty-principal semantics when no Subject is bound.
- Realm and SessionManager belong to runtime configuration, not the domain layer.
- Thread pools and request end must unbind the Shiro ThreadContext.
- Calibrate behavior with ShiroSubjectProviderTest/ShiroSubjectTest.
