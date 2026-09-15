# std.leb128

LEB128 (Little-Endian Base 128) variable-length integer encoding. Used in DWARF debug info, WASM, and Android serialization formats.

## Public API

Three functions for encoding unsigned/signed LEB128 values in fixed or variable-length buffers:

### Fixed-Length Write

```zig
// Write unsigned LEB128 into a fixed-size buffer
pub fn writeUnsignedFixed(comptime l: usize, ptr: *[l]u8, int: std.meta.Int(.unsigned, l * 7)) void

// Write signed LEB128 into a fixed-size buffer
pub fn writeSignedFixed(comptime l: usize, ptr: *[l]u8, int: std.meta.Int(.signed, l * 7)) void
```

- `l` — number of bytes in the output buffer (comptime)
- `ptr` — pointer to output buffer
- `int` — integer value to encode

### Variable-Length Write

```zig
pub fn writeUnsignedExtended(slice: []u8, arg: anytype) void
```

- `slice` — output buffer (should have enough space for the variable-length encoding)
- `arg` — integer value of any type

## How LEB128 Works

Each byte uses 7 bits for data and 1 bit (MSB) as a continuation flag:

```
Value: 624485
Binary: 0000 0000 0000 1001 1000 1010 1110 0110 0101
                                                      ↓
LEB128: 1110 0101  1011 1100  0010 0110  0000 0010
         E5          BC          26          02
```

- Bytes with MSB=1 continue to next byte
- Byte with MSB=0 is the final byte
- Signed LEB128 uses sign extension

## Example

```zig
const leb = std.leb128;

// Fixed 3-byte unsigned
var buf3: [3]u8 = undefined;
leb.writeUnsignedFixed(3, &buf3, 624485);

// Fixed 2-byte signed
var buf2: [2]u8 = undefined;
leb.writeSignedFixed(2, &buf2, -12345);

// Variable-length
var buf: [10]u8 = undefined;
leb.writeUnsignedExtended(&buf, @as(u64, 123456789));
```

## Gotchas

1. **Buffer size matters** — `writeUnsignedFixed(l)` panics if the value doesn't fit in `l` bytes. For unsigned, max value = 2^(l*7)-1.
2. **No read API** — std.leb128 only provides encoding. Decoding is done inline in consumers (DWARF, WASM readers).
3. **Signed values use sign extension** — negative numbers encode with leading 1-bits until the sign bit aligns with the MSB of the final byte.
