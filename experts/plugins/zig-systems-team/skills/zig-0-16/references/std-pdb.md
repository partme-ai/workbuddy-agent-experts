# std.pdb

PDB (Program Database) format types and structures — used for reading Windows debug symbol files.

## Quick Reference

```zig
const std = @import("std");
const pdb = std.pdb;
```

## Main Types

### MSF Superblock

```zig
pub const SuperBlock = extern struct {
    magic: [4]u8,         // "Microsoft C/C++ MSF 7.00\r\n\x1a\x44\x53"
    block_size: u32,      // size of each block (4096, 8192, etc.)
    free_block_map: u32,  // free block map index
    num_blocks: u32,      // total blocks
    num_directory_bytes: u32,
    unknown: u32,
    block_map_offset: u32, // block containing stream directory
};
```

The MSF (Multi-Stream File) format is the underlying container for PDB files.

### Stream Types

```zig
pub const StreamType = enum(u32) {
    pdb = 1,    // PDB info stream
    tpi = 2,    // Type information stream
    dbi = 3,    // Debug information stream
    ipi = 4,    // IPI (ID type) stream
    // ...
};
```

### DBI Stream Header

```zig
pub const DbiStreamHeader = extern struct {
    version_signature: u32,
    version_header: u32,
    age: u32,                 // incremental build count
    global_stream_index: u16,
    build_number: u16,
    public_stream_index: u16,
    pdb_dll_version: u16,
    sym_record_stream: u16,
    pdb_dll_rbld: u16,
    module_info_size: u32,
    section_contribution_size: u32,
    section_map_size: u32,
    src_info_size: u32,
    type_server_map_size: u32,
    mfc_type_server_index: u32,
    optional_dbg_header_size: u32,
    ec_substream_size: u32,
    flags: u16,
    machine: u16,
    padding: u32,
};
```

### Module Information

```zig
pub const ModInfo = extern struct {
    opened: u32,
    section_contribution: SectionContribEntry,
    flags: u16,
    module_stream_index: u16,
    symbol_size: u32,
    c11_size: u32,
    c13_size: u32,
    source_file_count: u16,
    padding: u16,
    // followed by module name (null-terminated) and object file name
};
```

### Symbol Records

```zig
pub const RecordPrefix = extern struct {
    rec_len: u16,           // record length
    rectyp: u16,            // record kind (SymbolKind)
};

pub const SymbolKind = enum(u16) {
    S_PUB = 0x1007,         // public symbol
    S_PROCREF = 0x0400,     // procedure reference
    S_LPROCREF = 0x0401,    // local procedure reference
    S_GDATA32 = 0x110C,     // global data (32-bit)
    S_LDATA32 = 0x110D,     // local data (32-bit)
    S_GTHREAD32 = 0x1112,   // global thread-local
    S_LTHREAD32 = 0x1113,   // local thread-local
    S_PUB32 = 0x1009,       // public symbol (32-bit)
    // ... many more
    _,
};

pub const ProcSym = extern struct {
    parent: u32, end: u32,
    next: u32, len: u32,
    dbg_start: u32, dbg_end: u32,
    token: u32, // type index
    off: u32,   // offset
    seg: u16,   // segment
    flags: ProcSymFlags,
    name: [1]u8, // variable-length
};
```

### Debug Subsections

```zig
pub const DebugSubsectionKind = enum(u32) {
    symbols = 0xF1,
    lines = 0xF2,
    string_table = 0xF3,
    file_checksums = 0xF4,
    frame_data = 0xF5,
    inlinee_lines = 0xF6,
    cross_scope_imports = 0xF7,
    cross_scope_exports = 0xF8,
    // ...
    _,
};

pub const DebugSubsectionHeader = extern struct {
    kind: DebugSubsectionKind,
    length: u32,
};
```

### Line Number Information

```zig
pub const LineNumberEntry = extern struct {
    code_offset: u32,
    line_and_flags: packed struct(u32) {
        start_line: u24,
        statement: u1,    // true = statement, false = expression
        end_line: u7,
    },
};

pub const ColumnNumberEntry = extern struct {
    start_column: u16,
    end_column: u16,
};
```

### Section Map

```zig
pub const SectionMapHeader = extern struct {
    count: u16,
    log_counts: u16,
};
pub const SectionMapEntry = extern struct { /* section flags, offsets */ };
```

### File Checksums

```zig
pub const FileChecksumEntryHeader = extern struct {
    name_offset: u32,
    checksum_size: u8,
    checksum_kind: u8,  // 0=None, 1=MD5, 2=SHA1, 3=SHA256
};
```

## Usage Context

`std.pdb` types are used by debuggers and tooling to parse Windows PDB symbols. In Zig's own toolchain, these are used by the DWARF-based debug info reader for Windows cross-debugging support.

## Gotchas

1. **PDB is Windows-only** — only useful when debugging Windows executables.
2. **MSF multi-stream format** — PDB files use a custom block-based container. Streams are accessed via block map indirection.
3. **Variable-length records** — Symbol names and module names are null-terminated variable-length fields after fixed struct headers.
4. **CodeView symbols** — `SymbolKind` follows the Microsoft CodeView symbol enumeration, which is different from DWARF.
5. **Most users don't need this** — `std.pdb` is primarily used by the Zig compiler and debugger implementations.
