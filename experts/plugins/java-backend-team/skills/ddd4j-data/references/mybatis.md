# MyBatis and MyBatis-Plus

> Collection date: 2026-09-11.

**Native track**: `Ddd4jMapper<P>` + `MybatisAggregateRepository`. Delete and production query SQL must be implemented explicitly.

**Plus track**: `BaseMapper<P>` + a same-named repository. `Query<M>` is translated into a Wrapper.

Shared rules: M / P / Q / ID generics, `DomainObjectMapper`, `RepositoryRegistry`, tenant / data scope / SQL observation. The two artifacts share package and class names — do not depend on both simultaneously.
