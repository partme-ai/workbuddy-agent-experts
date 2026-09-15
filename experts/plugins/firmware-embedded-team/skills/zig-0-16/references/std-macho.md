# std.macho

Mach-O (Mach Object) format constants, struct definitions, and parsers — used for reading macOS/iOS binary files.

## Quick Reference

```zig
const std = @import("std");
const macho = std.macho;
```

## Main Types

### File Headers

```zig
// 32-bit Mach-O header
pub const mach_header = extern struct {
    magic: u32,            // MH_MAGIC / MH_CIGAM
    cputype: u32,          // CPU_TYPE_X86, CPU_TYPE_ARM64, etc.
    cpusubtype: u32,
    filetype: u32,         // MH_OBJECT, MH_EXECUTE, MH_DYLIB, etc.
    ncmds: u32,            // number of load commands
    sizeofcmds: u32,
    flags: u32,
};

// 64-bit Mach-O header (adds reserved field)
pub const mach_header_64 = extern struct {
    magic: u32,
    cputype: u32,
    cpusubtype: u32,
    filetype: u32,
    ncmds: u32,
    sizeofcmds: u32,
    flags: u32,
    reserved: u32,
};
```

### Universal/Fat Binary

```zig
pub const fat_header = extern struct {
    magic: u32,            // FAT_MAGIC / FAT_CIGAM
    nfat_arch: u32,        // number of architectures
};

pub const fat_arch = extern struct {
    cputype: u32,
    cpusubtype: u32,
    offset: u32,
    size: u32,
    align: u32,
};
```

### Load Commands

```zig
pub const load_command = extern struct {
    cmd: u32,     // LC_* constant (see LC enum)
    cmdsize: u32, // total size of this command
};
```

| Struct | Load Command | Purpose |
|--------|-------------|---------|
| `segment_command_64` | `LC.SEGMENT_64` | Memory segment mapping |
| `symtab_command` | `LC.SYMTAB` | Symbol table |
| `dysymtab_command` | `LC.DYSYMTAB` | Dynamic symbol table |
| `dylib_command` | `LC.LOAD_DYLIB` | Dependent dylib |
| `rpath_command` | `LC.RPATH` | @rpath search path |
| `uuid_command` | `LC.UUID` | Build UUID |
| `entry_point_command` | `LC.MAIN` | Entry point |
| `build_version_command` | `LC.BUILD_VERSION` | Platform min OS version |
| `source_version_command` | `LC.SOURCE_VERSION` | Source version |
| `linkedit_data_command` | `LC.*_INFO_*` | LINKEDIT blobs |
| `dyld_info_command` | `LC.DYLD_INFO_ONLY` | Dyld rebase/bind/export |
| `dylinker_command` | `LC.LOAD_DYLINKER` | Dynamic linker path |

### LC Enum (Command Types)

```zig
pub const LC = enum(u32) {
    SEGMENT = 0x1,
    SYMTAB = 0x2,
    SYMSEG = 0x3,
    THREAD = 0x4,
    UNIXTHREAD = 0x5,
    LOAD_DYLIB = 0xc,
    ID_DYLIB = 0xd,
    LOAD_DYLINKER = 0xe,
    ID_DYLINKER = 0xf,
    SEGMENT_64 = 0x19,
    UUID = 0x1b,
    RPATH = 0x8000001c | 0x80000000,
    MAIN = 0x80000028 | 0x80000000,
    SOURCE_VERSION = 0x2a,
    BUILD_VERSION = 0x32,
    DYLD_INFO_ONLY = 0x80000022 | 0x80000000,
    // ... many more
};
```

### Segments and Sections

```zig
pub const segment_command_64 = extern struct {
    cmd: u32, cmd_size: u32,
    segname: [16]u8,
    vmaddr: u64, vmsize: u64,
    fileoff: u64, filesize: u64,
    maxprot: u32, initprot: u32,
    nsects: u32, flags: u32,
};

pub const section_64 = extern struct {
    sectname: [16]u8,
    segname: [16]u8,
    addr: u64, size: u64,
    offset: u32, align: u32,
    reloff: u32, nreloc: u32,
    flags: u32, reserved1: u32, reserved2: u32,
    reserved3: u32,
};
```

### Symbol Table

```zig
pub const nlist_64 = extern struct {
    n_strx: u32,     // string table index
    n_type: u8,      // type (stabs or N_EXT/N_PEXT)
    n_sect: u8,      // section number
    n_desc: u16,     // description (packed flags)
    n_value: u64,    // symbol value/address
};
```

### Load Command Iterator

```zig
pub const LoadCommandIterator = struct {
    pub fn next(it: *LoadCommandIterator) ?LoadCommand;
};

pub const LoadCommand = struct {
    header: load_command,
    data: []const u8,  // command-specific data after header
};
```

### Platform Enum

```zig
pub const PLATFORM = enum {
    MACOS, IOS, TVOS, WATCHOS, BRIDGEOS,
    MAC_CATALYST, IOS_SIMULATOR, TVOS_SIMULATOR, WATCHOS_SIMULATOR,
    DRIVERKIT,
};
```

### Relocation Types

```zig
pub const reloc_type_x86_64 = enum {
    UNSIGNED, SIGNED, BRANCH, GOT_LOAD, GOT, SUBTRACTOR, SIGNED_1, SIGNED_2,
    SIGNED_4, TLV,
};
pub const reloc_type_arm64 = enum {
    UNSIGNED, SUBTRACTOR, BRANCH26, PAGE21, PAGEOFF12, GOT_LOAD_PAGE21,
    GOT_LOAD_PAGEOFF12, POINTER_TO_GOT, TLV_PAGE21, TLV_PAGEOFF12,
    ADDEND, ARM64_32, TLV,
};
```

## Usage Example

```zig
const std = @import("std");

pub fn main() !void {
    const file = try std.fs.cwd().openFile("binary.dylib", .{});
    defer file.close();

    const hdr = try file.reader().readStruct(std.macho.mach_header_64);
    _ = hdr;

    var it = std.macho.LoadCommandIterator.init(file, hdr);
    while (try it.next()) |cmd| {
        if (cmd.header.cmd == @intFromEnum(std.macho.LC.SEGMENT_64)) {
            const seg = cmd.cast(std.macho.segment_command_64);
            std.debug.print("Segment: {s}\n", .{std.mem.sliceTo(&seg.segname, 0)});
        }
    }
}
```

## Gotchas

1. **Mach-O is macOS/iOS only** — not used on Linux or Windows.
2. **`nlist_64` type field encodes multiple things** — the type byte contains stabs marker (bit 5), N_EXT (bit 0), N_PEXT (bit 1), and type mask.
3. **Load command iteration is sequential** — commands are packed consecutively. Use `LoadCommandIterator` for safe traversal.
4. **Fat binaries contain multiple architectures** — check `fat_header.magic` first, then pick the matching arch slice.
5. **Segment names are 16-byte fixed** — use `std.mem.sliceTo(&name, 0)` for printing.
