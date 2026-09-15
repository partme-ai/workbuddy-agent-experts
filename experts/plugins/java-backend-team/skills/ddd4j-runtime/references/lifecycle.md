# Lifecycle

> Collection date: 2026-09-11.

validate → initialize → register → ready → drain → close. On failure, close only the resources that finished initialization, in reverse order. close can be called repeatedly. Request scope is restored on success, exception, and async completion.
