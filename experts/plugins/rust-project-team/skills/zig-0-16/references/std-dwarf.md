# std.dwarf

DWARF debugging information format constants. Used by debuggers (`std.debug.Dwarf`) to read debug info sections in ELF/Mach-O binaries.

## Quick Reference

```zig
const std = @import("std");
const dwarf = std.dwarf;
```

## Constant Modules

`std.dwarf` exports flat modules of DWARF specification constants. Each module groups related constants from the DWARF standard:

| Module | Prefix | Purpose | Example |
|--------|--------|---------|---------|
| `TAG` | `DW_TAG_*` | Debugging Information Entry tags | `compile_unit`, `subprogram`, `variable` |
| `AT` | `DW_AT_*` | Attribute names | `name`, `type`, `location`, `byte_size` |
| `FORM` | `DW_FORM_*` | Attribute form encodings | `string`, `data4`, `ref_addr`, `exprloc` |
| `OP` | `DW_OP_*` | Expression operation opcodes | `plus`, `minus`, `const1u`, `reg` |
| `LANG` | `DW_LANG_*` | Source language codes | `C`, `C89`, `C_plus_plus`, `Rust`, `Zig` |
| `ATE` | `DW_ATE_*` | Base type encodings | `unsigned`, `signed`, `float`, `address` |
| `LNS` | `DW_LNS_*` | Line number program opcodes | `copy`, `advance_pc`, `advance_line` |
| `LNE` | `DW_LNE_*` | Extended line number opcodes | `end_sequence`, `set_address`, `define_file` |
| `CFA` | `DW_CFA_*` | Call frame instruction opcodes | `advance_loc`, `def_cfa`, `offset` |
| `CC` | `DW_CC_*` | Calling convention | `normal`, `pass_by_reference` |
| `CHILDREN` | `DW_CHILDREN_*` | Child flag | `no` (0x00), `yes` (0x01) |
| `UT` | `DW_UT_*` | Unit type | `compile`, `type`, `partial` |
| `LLE` | `DW_LLE_*` | Location list entry kind | `end_of_list`, `base_addressx` |
| `RLE` | `DW_RLE_*` | Range list entry kind | `end_of_list`, `base_address` |
| `ACCESS` | `DW_ACCESS_*` | Accessibility | `public`, `protected`, `private` |

### Format Enum

```zig
pub const Format = enum { @"32", @"64" };
```

Used to distinguish 32-bit and 64-bit DWARF unit formats (affects header sizes).

### EH (Exception Handling) Constants

```zig
pub const EH = struct {
    pub const encoding: u8 = ...;
    pub const CFA: u8 = ...;
    pub const augmentation: []const u8 = ...;
    // ...
};
```

Exception handling frame constants for `.eh_frame` sections.

## Usage

```zig
const dwarf = std.dwarf;

// Check if a DIE tag is a subprogram
switch (tag) {
    dwarf.TAG.subprogram, dwarf.TAG.inlined_subroutine => {
        // is a function
    },
    else => {},
}

// Check attribute
switch (attr_name) {
    dwarf.AT.name => { /* read name */ },
    dwarf.AT.type => { /* resolve type */ },
    dwarf.AT.location => { /* evaluate expression */ },
    else => {},
}
```

## Relationship to std.debug.Dwarf

`std.dwarf` provides the **constants** (enums, opcodes, tags). The **parser** that uses these constants lives in `std.debug.Dwarf`:

```zig
// std.debug.Dwarf — the actual DWARF debug info parser
const DwarfInfo = std.debug.Dwarf;
var di = try DwarfInfo.init(allocator, .{ .debug_info = ..., .debug_abbrev = ... });
```

## Gotchas

1. **Constants only** — `std.dwarf` does NOT parse DWARF. It provides the enum values used by parsers like `std.debug.Dwarf`.
2. **`LNE.ZIG_set_decl`** — Zig adds a custom extended line opcode `DW_LNE_ZIG_set_decl` for inline declarations.
3. **Vendor extensions** — `CC` enum includes LLVM-specific calling conventions like `LLVM_ Swift`, `LLVM_ SwiftAsync`, `LLVM_ PreserveMost`.
4. **Frame info** — `.eh_frame` (exception handling) and `.debug_frame` (standard DWARF) use different CIE initial patterns. `EH` constants cover the `.eh_frame` variant.
