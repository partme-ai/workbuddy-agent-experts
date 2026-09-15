# Sa-Token

Entry points: StpKit, SaTokenSubject, SaTokenSubjectProvider, SaTokenSecurityConfigurer, SaTempKit, ApiKeyKit.

- Use StpKit.DEFAULT/ADMIN/USER to keep the account system consistent.
- Extended fields go through AuthConstants and type-safe getters.
- SaTempToken uses a short TTL, single use, and delete/verify.
- SaMixCheckLogin/SaInternalCheck need handler behavior tests.
- At request end, verify Subject and Sa-Token context cleanup.
