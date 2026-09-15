# std.wasm

WebAssembly binary format constants and types — used for encoding/decoding WASM modules.

## Quick Reference

```zig
const std = @import("std");
const wasm = std.wasm;
```

## Constants

```zig
wasm.magic          // \0asm — WASM module magic bytes
wasm.version        // version 1 (32-bit little-endian)
wasm.page_size      // 64 * 1024 (64 KiB per WASM page)
wasm.element_type   // 0x70 — funcref
wasm.function_type  // 0x60
wasm.result_type    // 0x40
```

## Types

### Opcodes

```zig
pub const Opcode = enum(u8) {
    unreachable = 0x00,
    nop = 0x01,
    block = 0x02,
    loop = 0x03,
    @"if" = 0x04,
    @"else" = 0x05,
    end = 0x0b,
    br = 0x0c,
    br_if = 0x0d,
    br_table = 0x0e,
    @"return" = 0x0f,
    call = 0x10,
    call_indirect = 0x11,
    drop = 0x1a,
    select = 0x1b,
    local_get = 0x20,
    local_set = 0x21,
    local_tee = 0x22,
    global_get = 0x23,
    global_set = 0x24,
    i32_load = 0x28,
    i64_load = 0x29,
    f32_load = 0x2a,
    f64_load = 0x2b,
    i32_store = 0x36,
    i64_store = 0x37,
    f32_store = 0x38,
    f64_store = 0x39,
    memory_size = 0x3f,
    memory_grow = 0x40,
    i32_const = 0x41,
    i64_const = 0x42,
    f32_const = 0x43,
    f64_const = 0x44,
    i32_eqz = 0x45,
    i32_eq = 0x46,
    i32_ne = 0x47,
    i32_lt_s = 0x48,
    i32_lt_u = 0x49,
    i32_gt_s = 0x4a,
    i32_gt_u = 0x4b,
    i32_le_s = 0x4c,
    i32_le_u = 0x4d,
    i32_ge_s = 0x4e,
    i32_ge_u = 0x4f,
    // ... full WASM spec opcodes
};
```

### Value Types

```zig
pub const Valtype = enum(u8) {
    i32 = 0x7f,
    i64 = 0x7e,
    f32 = 0x7d,
    f64 = 0x7c,
    v128 = 0x7b,
    @"externref" = 0x6f,
    funcref = 0x70,
};
```

### Section Types

```zig
pub const Section = enum(u8) {
    custom = 0,
    type = 1,
    import = 2,
    function = 3,
    table = 4,
    memory = 5,
    global = 6,
    @"export" = 7,
    start = 8,
    element = 9,
    code = 10,
    data = 11,
    data_count = 12,
};
```

### Other Types

```zig
pub const RefType = enum(u8) { funcref = 0x70, externref = 0x6f };
pub const ExternalKind = enum(u8) { func = 0, table = 1, mem = 2, global = 3 };
pub const BlockType = enum(u8) { empty = 0x40 };

pub const Limits = struct {
    flags: u8,
    min: u32,
    max: u32,  // only valid if flags & 1
};

pub const Memory = struct { limits: Limits };
pub const InitExpression = union { ... };
```

### Multi-Byte Opcodes

```zig
pub const MiscOpcode = enum(u8) { ... };     // 0xFC prefix
pub const SimdOpcode = enum(u8) { ... };     // 0xFD prefix
pub const AtomicsOpcode = enum(u8) { ... };  // 0xFE prefix
```

## Usage

`std.wasm` is primarily used by the Zig compiler's WASM backend and by WASM inspection tools:

```zig
const std = @import("std");

// Check WASM magic
const header = try file.reader().readBytesAlloc(allocator, 8);
if (!std.mem.eql(u8, header[0..4], &std.wasm.magic)) {
    std.debug.print("Not a WASM file\n", .{});
    return;
}
```

## Gotchas

1. **Compile-time constants only** — `std.wasm` provides type/enum constants for the WASM binary format, not a runtime WASM VM.
2. **Used by the compiler** — Zig's WASM backend uses these types to emit .wasm files.
3. **Multi-byte opcodes** — SIMD (`SimdOpcode`) and atomics (`AtomicsOpcode`) use the 0xFD/0xFE prefixes; check the prefix byte first, then the secondary opcode.
4. **`page_size`** — every WASM memory page is 64 KiB. `memory.grow` operates in page units.
