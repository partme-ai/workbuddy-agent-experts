# std.Target

CPU architecture, OS, and ABI target detection — used for cross-compilation and platform-specific code.

## Quick Reference

```zig
const std = @import("std");
const target = @import("builtin").target;  // current target

// Or in build.zig:
const query: std.Target.Query = .{ .cpu_arch = .x86_64, .os_tag = .linux };
const resolved = b.resolveTargetQuery(query);
```

## Target.Query

Used to describe a target in `build.zig`:

```zig
pub const Query = struct {
    cpu_arch: ?std.Target.Cpu.Arch = null,
    os_tag: ?std.Target.Os.Tag = null,
    abi: ?std.Target.Abi = null,
    cpu_model: ?std.Target.Cpu.Model = null,
    cpu_features_add: std.Target.Cpu.Feature.Set = .{},
    cpu_features_sub: std.Target.Cpu.Feature.Set = .{},
    os_version_min: ?std.Target.Os.Version = null,
    os_version_max: ?std.Target.Os.Version = null,
    glibc_version: ?std.Target.Os.Version = null,
    ofmt: ?std.Target.ObjectFormat = null,
};
```

### Common Queries

```zig
// Native target (default)
const native: std.Target.Query = .{};

// Linux x86_64
const linux_x64: std.Target.Query = .{ .cpu_arch = .x86_64, .os_tag = .linux };

// macOS ARM64
const macos_arm64: std.Target.Query = .{ .cpu_arch = .aarch64, .os_tag = .macos };

// Windows x86_64
const win_x64: std.Target.Query = .{ .cpu_arch = .x86_64, .os_tag = .windows };

// WebAssembly
const wasm: std.Target.Query = .{ .cpu_arch = .wasm32, .os_tag = .freestanding };

// Linux ARM with soft float
const arm_linux: std.Target.Query = .{ .cpu_arch = .arm, .os_tag = .linux, .abi = .gnueabihf };

// With specific CPU features
const avx2_x64: std.Target.Query = .{
    .cpu_arch = .x86_64,
    .os_tag = .linux,
    .cpu_features_add = std.Target.x86.featureSet(&.{ .avx2, .fma }),
};
```

## ResolvedTarget

```zig
pub const ResolvedTarget = struct {
    result: Target,       // resolved target info
    is_native: bool,      // is this the build machine?
};

pub const Target = struct {
    cpu: Cpu,
    os: Os,
    abi: Abi,
    ofmt: ObjectFormat,
};
```

### At Compile Time

```zig
const builtin = @import("builtin");

// OS detection
if (builtin.target.os_tag == .linux) { /* Linux */ }
if (builtin.target.os_tag == .windows) { /* Windows */ }

// Architecture detection
if (builtin.target.cpu_arch == .x86_64) { /* 64-bit x86 */ }

// Object format
if (builtin.target.ofmt == .elf) { /* ELF binary */ }

// Endianness
if (builtin.target.cpu.endian() == .little) { /* Little endian */ }
```

## Key Enums

### Os.Tag (Operating Systems)

```zig
.linux, .macos, .windows, .freebsd, .netbsd, .openbsd,
.dragonfly, .solaris, .haiku, .plan9, .wasi, .freestanding,
.uefi, .emscripten, .ananas, .cloudabi, .fuchsia, .kfreebsd,
.onyx, .zos, .other,
```

### Cpu.Arch (Architectures)

```zig
.x86_64, .aarch64, .arm, .wasm32, .wasm64, .riscv32, .riscv64,
.x86, .powerpc, .powerpc64, .powerpc64le, .sparc64, .spirv32,
.spirv64, .mips, .mipsel, .mips64, .mips64el, .s390x,
.hexagon, .avr, .msp430, .nvptx64, .bpfel, .bpfeb,
.amdgcn, .loongarch64, .csky, .arc, .kalimba,
```

### Abi (ABI variants)

```zig
.none, .gnu, .gnueabihf, .gnuilp, .musl, .musleabihf,
.musleabi, .eabi, .android, .msvc, .itanium, .cygnus,
.simulator, .macabi, .pixel, .elfv1, .elfv2,
```

### ObjectFormat

```zig
.elf, .macho, .coff, .wasm, .c, .plan9, .spirv,
```

## Target Specifics

### CPU Feature Sets

```zig
// x86 features
const x86_features = std.Target.x86.featureSet(&.{ .avx2, .sse4_2, .aes });

// ARM features
const arm_features = std.Target.aarch64.featureSet(&.{ .neon, .crypto });

// Check if feature is supported
const has_avx = std.Target.x86.featureSetHas(builtin.target.cpu.features, .avx);
```

### OS Version Constraints

```zig
const query: std.Target.Query = .{
    .cpu_arch = .aarch64,
    .os_tag = .macos,
    .os_version_min = .{ .semver = .{ .major = 11, .minor = 0, .patch = 0 } },
};
```

## Gotchas

1. **`builtin.target` vs `std.Target.Query`** — `builtin.target` is the current compile target; `Query` is for describing a desired target in build.zig.
2. **Cross-compilation requires `-Dtarget`** — `zig build -Dtarget=aarch64-linux` changes the target; `builtin.target` reflects this.
3. **CPU feature sets are architecture-specific** — `std.Target.x86.featureSet()` only works for x86 targets; use the correct arch namespace.
4. **`.freestanding` means no OS** — used for bare-metal, kernels, and WebAssembly without WASI.
