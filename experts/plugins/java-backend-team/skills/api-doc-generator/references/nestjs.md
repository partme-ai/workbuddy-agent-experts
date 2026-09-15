# NestJS API discovery

## Locate routes

- Find `@Controller` prefixes and method decorators such as `@Get`, `@Post`, `@Put`, `@Patch`, and `@Delete`.
- Include global prefixes, URI versioning, module routing, and controller version metadata.

## Resolve contracts

- Read `@Param`, `@Query`, `@Headers`, `@Body`, `@UploadedFile`, and DTO classes.
- Resolve class-validator and class-transformer decorators.
- Use Swagger decorators when present, but compare them with implementation and DTO validation.

## Security and errors

- Inspect guards, interceptors, pipes, filters, and global configuration.
- Record roles/scopes only when supported by guard or decorator evidence.
- Include exception filter behavior and tested status codes.
