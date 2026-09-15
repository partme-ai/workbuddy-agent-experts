# Anti-Patterns

> Collection date: 2026-09-11.

1. **Line-name misreading**: treating 4.0.x as Quarkus 4; read the BOM.
2. **Spring projection**: work within the Quarkus build-time/CDI model.
3. **BOM as runtime**: verify beans/BuildItems.
4. **Container as success**: require real behavior.
5. **Security false green**: SKIPPED does not equal PASS.
