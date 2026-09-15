# std.coff

COFF (Common Object File Format) and PE (Portable Executable) constants, struct definitions, and parsers — used for reading Windows binary files.

## Quick Reference

```zig
const std = @import("std");
const coff = std.coff;
```

## Main Types

### File Header

```zig
pub const Header = extern struct {
    machine: u16,         // Machine type (see IMAGE.FILE.MACHINE)
    number_of_sections: u16,
    time_date_stamp: u32,
    pointer_to_symbol_table: u32,
    number_of_symbols: u32,
    size_of_optional_header: u16,
    characteristics: Flags,  // packed struct
};
```

### PE Optional Header

```zig
pub const OptionalHeader = extern struct {
    magic: u16,          // 0x10b (PE32) or 0x20b (PE32+)
    major_linker_version: u8,
    minor_linker_version: u8,
    size_of_code: u32,
    address_of_entry_point: u32,
    base_of_code: u32,
    // ... PE32 vs PE32+ differ from here
};
```

### Section Header

```zig
pub const SectionHeader = extern struct {
    name: [8]u8,
    virtual_size: u32,
    virtual_address: u32,
    size_of_raw_data: u32,
    pointer_to_raw_data: u32,
    pointer_to_relocations: u32,
    pointer_to_linenumbers: u32,
    number_of_relocations: u16,
    number_of_linenumbers: u16,
    characteristics: u32,
};
```

### Symbol Table

```zig
pub const Symbol = extern struct {
    name: extern union {
        short_name: [8]u8,   // if name fits in 8 bytes
        offset: struct {     // if longer — points to string table
            zeroes: u32,
            offset: u32,
        },
    },
    value: u32,
    section_number: i16,     // use SectionNumber enum
    sym_type: u16,           // SymType: base + complex type
    storage_class: u8,       // StorageClass enum
    number_of_aux_symbols: u8,
};
```

### Enums

| Enum | Purpose | Example Values |
|------|---------|---------------|
| `Subsystem` | Windows subsystem | `GUI`, `CUI`, `NATIVE`, `EFI_*` |
| `SectionNumber` | Special section indices | `UNDEFINED`, `ABSOLUTE`, `DEBUG` |
| `StorageClass` | Symbol storage class | `EXTERNAL`, `STATIC`, `FUNCTION` |
| `DebugType` | Debug directory type | `CODEVIEW`, `COFF`, `PDB` |

### Parsing with `Coff`

```zig
pub const Coff = struct {
    header: Header,
    optional_header: ?OptionalHeader,
    sections: []const SectionHeader,
    strtab: Strtab,
    symtab: Symtab,
    // ...
};
```

```zig
const coff_file = try std.coff.Coff.parse(file, allocator);
defer coff_file.deinit(allocator);

std.debug.print("Sections: {d}\n", .{coff_file.header.number_of_sections});
std.debug.print("Symbols: {d}\n", .{coff_file.symtab.len()});
```

### Symbol Table Iteration

```zig
var it = coff_file.symtab.iterator();
while (it.next()) |sym| {
    const name = try coff_file.strtab.getName(sym.name.offset.offset);
    std.debug.print("Symbol: {s}\n", .{name});
}
```

### Relocation Types

```zig
// Per-architecture relocation type enums
coff.REL.I386    // x86 relocations
coff.REL.AMD64   // x64 relocations
coff.REL.ARM     // ARM relocations
coff.REL.ARM64   // ARM64 relocations
```

### Import/Export

```zig
// Import directory
const import_dir = coff.ImportDirectoryEntry { .lookup_table_rva = ..., .name_rva = ..., .iat_rva = ... };

// Base relocations (ASLR fixups)
const reloc = coff.BaseRelocation { ... };
const reloc_type = coff.BaseRelocationType;  // ABSOLUTE, HIGH, LOW, HIGHLOW, DIR64, ...
```

### COMDAT (Identical COMDAT Folding)

```zig
pub const ComdatSelection = enum {
    no_duplicates,
    any,
    same_size,
    exact_match,
    associative,
    largest,
    newcomer,
};
```

## Usage Example

```zig
const std = @import("std");

pub fn main() !void {
    const file = try std.fs.cwd().openFile("binary.exe", .{});
    defer file.close();

    const coff_file = try std.coff.Coff.parse(file, std.heap.page_allocator);
    defer coff_file.deinit(std.heap.page_allocator);

    std.debug.print("Machine: 0x{x}\n", .{coff_file.header.machine});
    std.debug.print("Sections: {d}\n", .{coff_file.sections.len});

    for (coff_file.sections, 0..) |sec, i| {
        const name = std.mem.sliceTo(&sec.name, 0);
        std.debug.print("  [{d}] {s} size={d}\n", .{ i, name, sec.size_of_raw_data });
    }
}
```

## Gotchas

1. **COFF handles Windows-only** — PE/COFF is the native format for Windows executables and DLLs.
2. **`Coff.parse`** reads the entire file — for very large files, use manual header reading with the iterators.
3. **String table** — symbol names longer than 8 bytes are stored in the string table; access via `Strtab.getName()`.
4. **PE32 vs PE32+** — `OptionalHeader` has different layouts for 32-bit (PE32) and 64-bit (PE32+) binaries. Check `magic` field.
5. **Section names are 8-byte fixed** — use `std.mem.sliceTo(&name, 0)` to get a proper string.
