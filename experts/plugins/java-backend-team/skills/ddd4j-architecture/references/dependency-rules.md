# Dependency Rules

1. Dependency arrows flow from adapters toward core ports.
2. Domain must not depend on framework entities, Wrappers, or HTTP context.
3. Runtime is responsible for registering CommandBus, Publisher, SubjectProvider, and similar components into the SPI.
4. Data performs explicit mapping between Domain and PO.
5. Web binds and releases Context/Subject at the request boundary.
6. MQ and Cache implementations must declare single-node, cluster, and atomic semantics.
7. Parent/BOM manage the build; they do not substitute for functional implementation.
