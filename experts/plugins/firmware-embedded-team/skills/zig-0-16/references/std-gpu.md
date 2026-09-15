# std.gpu

GPU abstraction types — SPIR-V execution mode definitions for shader programming.

## Quick Reference

```zig
const std = @import("std");
const gpu = std.gpu;
```

## Main Types

### ExecutionMode

```zig
pub const ExecutionMode = union(Tag) {
    origin_upper_left,
    origin_lower_left,
    depth_replacing,
    depth_greater,
    depth_less,
    depth_unchanged,
    local_size: LocalSize,

    pub const Tag = enum {
        origin_upper_left,
        origin_lower_left,
        depth_replacing,
        depth_greater,
        depth_less,
        depth_unchanged,
        local_size,
    };
};
```

Represents SPIR-V execution modes for shader entry points:

| Variant | SPIR-V Enum | Purpose |
|---------|-------------|---------|
| `origin_upper_left` | OriginUpperLeft | Framebuffer origin (Vulkan default) |
| `origin_lower_left` | OriginLowerLeft | Framebuffer origin (OpenGL) |
| `depth_replacing` | DepthReplacing | Fragment shader sets depth |
| `depth_greater` | DepthGreater | Fragment depth > default |
| `depth_less` | DepthLess | Fragment depth < default |
| `depth_unchanged` | DepthUnchanged | Fragment depth unchanged |
| `local_size` | LocalSize | Compute shader workgroup size |

### LocalSize

```zig
pub const LocalSize = struct {
    x: u32,
    y: u32,
    z: u32,
};
```

Workgroup dimensions for compute shaders.

## Helper Functions

```zig
// Generate SPIR-V location decoration with value
pub fn location(location: u32) BuiltIn;

// Generate SPIR-V binding decoration with value
pub fn binding(binding: u32) BuiltIn;

// Generate SPIR-V execution mode decoration
pub fn executionMode(mode: ExecutionMode) BuiltIn;
```

These return `BuiltIn` types used by Zig's SPIR-V backend for GPU code generation.

## Usage Context

`std.gpu` is used with Zig's SPIR-V backend for GPU/shaders:

```zig
pub const shader = struct {
    pub fn main(@gpu.location(0) input: f32) @gpu.builtin()
};
```

The declarations in `std.gpu` are consumed by the Zig compiler's SPIR-V code generation path — they are not runtime APIs.

## Gotchas

1. **Compile-time only** — `std.gpu` types are used during compilation for SPIR-V generation, not at runtime.
2. **SPIR-V backend required** — these types are only meaningful when targeting `.spirv` or using GPU-enabled targets.
3. **Limited scope** — `std.gpu` does NOT provide GPU runtime APIs (no Vulkan/Metal/DirectX wrappers). It only covers SPIR-V execution mode decorations.
4. **Experimental** — The GPU/SPIR-V backend is still evolving in Zig. API may change.
