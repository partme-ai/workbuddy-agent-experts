# Subject Lifecycle

1. Authenticate at the request entry point.
2. The Provider constructs the ddd4j Subject.
3. Web/Runtime binds the ThreadContext or request scope.
4. The application layer reads only Subject/SubjectKit.
5. finally/scope close restores the previous context.
6. Test logout, exceptions, async, and thread reuse.

Never leak the previous request's Subject into the next request.
