# Spring API discovery

## Locate routes

- Find `@RestController`, `@Controller`, router functions, and class/method `@RequestMapping` variants.
- Combine servlet context path, API prefix, class mapping, and method mapping.
- Include composed annotations and inherited interfaces when used.

## Resolve requests

- Map `@PathVariable`, `@RequestParam`, `@RequestHeader`, `@CookieValue`, `@RequestPart`, and `@RequestBody`.
- Read Bean Validation constraints, Jackson naming/ignore rules, Kotlin nullability, records, and Lombok-generated accessors.
- Account for `Pageable`, multipart forms, and content negotiation.

## Resolve responses and errors

- Unwrap `ResponseEntity`, reactive types, futures, and application response envelopes.
- Inspect `@ResponseStatus`, `@ExceptionHandler`, `@ControllerAdvice`, security configuration, filters, and tests.
- Do not infer a status code only from a method name.
