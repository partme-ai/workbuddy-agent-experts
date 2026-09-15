# Example 1 — Event-sourced aggregate

## Prompt

> We need an order aggregate where the full state history matters for audit. Using ddd4j 2.0.x on Java 17, show me how to build it and how to persist it.

## What the skill should do

1. Confirm the line is `2.0.x` (Java 17, Maven 3, POM 4.0) before quoting any API.
2. Read the current `AggregateRoot`, `DomainEvent`, and `Repository` source in that line.
3. Model the aggregate with Active Record **or** Event Sourcing — here Event Sourcing, because history is required.
4. Show `registerEvent(...)` in the command method and `@EventHandler` for the apply method.
5. State that persistence must call `pullDomainEvents()` and must **not** also call snapshot-style `save()` / `update()`.

## Expected output

```java
public final class Order extends AggregateRoot<OrderId> {
    private OrderStatus status;

    public void pay() {
        if (status == OrderStatus.PAID) {
            throw new IllegalStateException("Order already paid");
        }
        registerEvent(new OrderPaid(id()));
    }

    @EventHandler
    void apply(OrderPaid event) {
        status = OrderStatus.PAID;
    }
}
```

Plus a statement of the evidence tier: source read (which files), tests run (event replay), and the remaining gap (no real-database verification yet).

## Failure the skill must avoid

Recommending `save()` alongside `pullDomainEvents()`. That mixes persistence tracks on one aggregate and is the most common ddd4j-core mistake.
