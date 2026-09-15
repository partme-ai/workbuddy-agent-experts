# std.elf

ELF (Executable and Linkable Format) constants, struct definitions, and parsers — used for reading Linux/Unix binary files.

## Quick Reference

```zig
const std = @import("std");
const elf = std.elf;
```

## Main Types

### Enums (Constants)

| Enum | Purpose | Example Values |
|------|---------|---------------|
| `ET` | File type | `REL`, `EXEC`, `DYN`, `CORE` |
| `EM` | Machine architecture | `X86_64`, `ARM`, `RISCV`, `AARCH64` |
| `CLASS` | 32/64 bit | `@"32"`, `@"64"` |
| `DATA` | Endianness | `2LSB` (little), `2MSB` (big) |
| `OSABI` | OS/ABI | `GNU`, `FREEBSD`, `SOLARIS` |
| `PT` | Program header type | `LOAD`, `DYNAMIC`, `TLS`, `GNU_STACK` |
| `SHT` | Section header type | `PROGBITS`, `SYMTAB`, `STRTAB`, `NOBITS` |
| `STB` | Symbol binding | `LOCAL`, `GLOBAL`, `WEAK` |
| `STT` | Symbol type | `NOTYPE`, `OBJECT`, `FUNC`, `TLS` |
| `STV` | Symbol visibility | `DEFAULT`, `HIDDEN` |
| `COMPRESS` | Compression | `ZLIB`, `ZSTD` |

### Structs (Raw Headers)

| Struct | Size | Purpose |
|--------|------|---------|
| `Elf64.Ehdr` | 64 bytes | ELF header (magic, entry, phoff, shoff) |
| `Elf64.Phdr` | 56 bytes | Program header (type, vaddr, memsz, flags) |
| `Elf64.Shdr` | 64 bytes | Section header (name, type, offset, size) |
| `Elf64.Sym` | 24 bytes | Symbol table entry |
| `Elf64.Rela` | 24 bytes | Relocation with addend |
| `Elf64.Dyn` | 16 bytes | Dynamic section entry |

32-bit variants (`Elf32.*`) also exist with smaller struct sizes.

### Parsed Header

```zig
const header = try elf.Header.read(file);
// header.is_64, header.endian, header.type,
// header.machine, header.entry, ...
```

### Iterators

```zig
// Program headers
var ph_it = try elf.ProgramHeaderIterator.init(file, header);
while (try ph_it.next()) |ph| { _ = ph; }

// Section headers
var sh_it = try elf.SectionHeaderIterator.init(file, header);
while (try sh_it.next()) |sh| { _ = sh; }

// Dynamic section entries
var dyn_it = try elf.DynamicSectionIterator.init(file, header);
while (try dyn_it.next()) |dyn| { _ = dyn; }
```

Buffer-based iterators also exist without file I/O:

```zig
var ph_it = elf.ProgramHeaderBufferIterator.init(buffer, offset);
var sh_it = elf.SectionHeaderBufferIterator.init(buffer, offset);
```

### Packed Flags

```zig
// Section header flags
const shf: elf.SHF = .{ .WRITE = true, .ALLOC = true, .EXECINSTR = true };

// Program header flags
const pf: elf.PF = .{ .X = true, .W = true, .R = true };
```

### Special Constants

```zig
elf.MAGIC       // "\x7fELF" — magic bytes
elf.SHN_UNDEF   // 0 — undefined section index
elf.SHN_ABS     // 0xFFF1 — absolute value
elf.SHN_COMMON  // 0xFFF2 — common symbol

// Auxiliary vector types
elf.AT_PHDR     // address of program headers
elf.AT_ENTRY    // entry point
elf.AT_PAGESZ   // system page size
elf.AT_RANDOM   // random bytes for stack canary
elf.AT_CLKTCK   // clock ticks per second

// Dynamic tags
elf.DT_NULL     // end of dynamic section
elf.DT_NEEDED   // needed library (string table index)
elf.DT_SYMTAB   // symbol table address
elf.DT_STRTAB   // string table address
elf.DT_INIT     // init function
elf.DT_DEBUG    // debug info
```

## Usage Example

```zig
const std = @import("std");

pub fn main() !void {
    const file = try std.fs.cwd().openFile("binary.elf", .{});
    defer file.close();

    const header = try std.elf.Header.read(file);
    std.debug.print("ELF: {s} {s}\n", .{
        @tagName(header.machine),
        @tagName(header.type),
    });

    var it = try std.elf.ProgramHeaderIterator.init(file, header);
    while (try it.next()) |ph| {
        if (ph.p_type == elf.PT.LOAD) {
            std.debug.print("LOAD segment: vaddr=0x{x}, memsz={d}\n", .{
                ph.p_vaddr,
                ph.p_memsz,
            });
        }
    }
}
```

## Gotchas

1. **ELF types have raw and parsed forms** — `Elf64.Ehdr` is the raw C struct, `Header` is the parsed Zig struct with nicer fields.
2. **Iterators require positioned reads** — use `file.seekTo()` or the buffer-based iterators for in-memory data.
3. **Enums vs constants** — Old code uses raw constants like `PT_LOAD`. New code should use `@intFromEnum(elf.PT.LOAD)` or compare with enum values directly.
4. **Endianness** — Header-based iterators handle endianness; raw structs may need byte swapping for big-endian files.
