# Example 5 — Green context, zero consumers

## Prompt

> We deployed the new service and the app is healthy, dashboards are green — but the downstream team says they've been sending events for an hour and we've processed none. No errors in our logs. What broke?

## What the skill should do

1. Recognize the signature: healthy app plus zero consumption equals listener scanning found nothing — the context starts fine with an empty registrar.
2. Check the listener registrar on the line: how listeners are discovered (scanning vs explicit registration) and whether the discovery condition excluded them (wrong package, missing marker interface, disabled property).
3. Verify the consumer group/topic bindings from the broker side — an empty consumer group with an active topic confirms nothing subscribed.
4. Check whether the required-listener startup gate was configured; its absence is why the deploy went out green with zero listeners.
5. Fix the discovery path, make the listener required if that matches the deployment intent, and add a startup assertion that expected listeners are registered.

## Expected output

```
Broker side: topic active, producer sending, consumer group <group>
             has 0 members ← nothing subscribed

Application side: context green, no errors, MQ beans created.

Diagnosis: listener registrar scanned 0 listeners — the listeners live
outside the scanned package, so registration silently found nothing.
The context does not fail on an empty scan (required-listener gate off).

Fix:
  1. correct the scan base / marker so listeners register
  2. mark the order-events listener required → misconfiguration now
     blocks startup
  3. startup log asserts registered-listener count == expected

Evidence: SOURCE (registrar read) + broker-side observation.
Post-fix round-trip test: NOT RUN yet.
```

## Failure the skill must avoid

Restarting the app or scaling pods hoping it heals. Zero registered listeners is a wiring condition, not a transient broker fault — every restart comes up equally green and equally deaf.
