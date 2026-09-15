# std.base64

Base64 encoding/decoding per RFC 4648. Multiple codec variants for different use cases.

## Quick Reference

| Codec | Alphabet | Padding | Use Case |
|-------|----------|---------|----------|
| `standard` | `A-Za-z0-9+/` | `=` | Email, MIME, general |
| `standard_no_pad` | `A-Za-z0-9+/` | none | Compact storage |
| `url_safe` | `A-Za-z0-9-_` | `=` | URL parameters |
| `url_safe_no_pad` | `A-Za-z0-9-_` | none | JWT, cookies, filenames |

## Encoding

### To Buffer

```zig
const std = @import("std");

const data = "Hello, World!";

// Calculate required size first
const size = std.base64.standard.Encoder.calcSize(data.len);
var buf: [size]u8 = undefined;
const encoded = std.base64.standard.Encoder.encode(&buf, data);
// "SGVsbG8sIFdvcmxkIQ=="

// URL-safe without padding (compact, no URL escaping needed)
const encoded_url = std.base64.url_safe_no_pad.Encoder.encode(&buf, data);
// "SGVsbG8sIFdvcmxkIQ"
```

### To Allocated String

```zig
const encoded = try allocator.alloc(u8, std.base64.standard.Encoder.calcSize(data.len));
_ = std.base64.standard.Encoder.encode(encoded, data);
```

### Streaming Write

```zig
var buf: [4096]u8 = undefined;
var w: std.Io.Writer = .fixed(&buf);
try std.base64.standard.Encoder.encodeWriter(&w, data);
const result = w.buffered();
```

## Decoding

### From Buffer

```zig
const encoded = "SGVsbG8sIFdvcmxkIQ==";

// Calculate decoded size
const decoded_len = try std.base64.standard.Decoder.calcSizeForSlice(encoded);

var buf: [decoded_len]u8 = undefined;
try std.base64.standard.Decoder.decode(&buf, encoded);
// buf = "Hello, World!"
```

### Max Size Estimation

```zig
// Before knowing padding amount
const max = try std.base64.standard.Decoder.calcSizeUpperBound(encoded.len);
var buf: [max]u8 = undefined;
const actual_len = try std.base64.standard.Decoder.decode(buf[0..], encoded);
const decoded = buf[0..actual_len];
```

### With Ignored Characters

Useful for PEM files, multi-line Base64, or whitespace-tolerant decoding:

```zig
const pem_data = "SGVs bG8s\nIFdv cmxk IQ==";  // spaces and newlines

const decoder = std.base64.standard.decoderWithIgnore(" \n\r");

const max = try decoder.calcSizeUpperBound(pem_data.len);
var buf: [max]u8 = undefined;
const len = try decoder.decode(buf[0..max], pem_data);
// buf[0..len] = "Hello, World!"
```

### Streaming Read

```zig
var buf: [4096]u8 = undefined;
var r: std.Io.Reader = .fixed(encoded_data);
try std.base64.standard.Decoder.decodeReader(&r, &buf);
```

## Error Handling

```zig
std.base64.standard.Decoder.decode(dest, source) catch |err| switch (err) {
    error.InvalidCharacter => { /* character not in alphabet */ },
    error.InvalidPadding => { /* incorrect = padding */ },
    error.NoSpaceLeft => { /* dest too small (decoderWithIgnore only) */ },
};
```

## Alphabet Access

```zig
// Direct access to alphabet character tables
std.base64.standard_alphabet_chars   // [64]u8 — "A-Za-z0-9+/"
std.base64.url_safe_alphabet_chars   // [64]u8 — "A-Za-z0-9-_"

// Inverse lookup tables (for manual implementation)
std.base64.standard_map_char_to_6_bits   // [128]u6
std.base64.url_safe_map_char_to_6_bits   // [128]u6
```

## Common Patterns

### JWT Payload Decode

```zig
fn decodeJwtPayload(payload: []const u8, buf: []u8) ![]u8 {
    const decoder = std.base64.url_safe_no_pad.Decoder;
    const size = try decoder.calcSizeForSlice(payload);
    try decoder.decode(buf[0..size], payload);
    return buf[0..size];
}
```

### PEM Format Decode

```zig
fn decodePem(pem: []const u8, buf: []u8) ![]u8 {
    // Find Base64 content between header/footer
    const start = std.mem.indexOf(u8, pem, "-----BEGIN") orelse 0;
    const b64 = std.mem.trim(u8, pem[start..], &[_]u8{'\n', '\r', '-'});
    const decoder = std.base64.standard.decoderWithIgnore("\n\r");
    const max = try decoder.calcSizeUpperBound(b64.len);
    return buf[0..try decoder.decode(buf[0..max], b64)];
}
```

### Encode Binary for URL

```zig
fn encodeUrlSafe(data: []const u8, buf: []u8) []const u8 {
    return std.base64.url_safe_no_pad.Encoder.encode(buf, data);
}
```

## Performance Characteristics

| Operation | Complexity | Allocations |
|-----------|------------|-------------|
| `encode(buf, data)` | O(n) | 0 (fixed buffer) |
| `decode(dest, src)` | O(n) | 0 (fixed buffer) |
| `calcSize(n)` | O(1) | 0 |
| `calcSizeForSlice(s)` | O(n) | 0 |
| `encodeWriter(w, data)` | O(n) | 0 |

## Gotchas

1. **Output buffer must be large enough** — `encode` does NOT check bounds. Use `calcSize` first.
2. **`calcSizeForSlice` scans the input** — it looks for padding. For untrusted input, consider `calcSizeUpperBound` + a sufficient buffer.
3. **Padding character `=`** — URL-safe variants use `=` too. Use `no_pad` variants to omit padding.
4. **Standard uses `+` and `/`** — these must be URL-encoded in URLs (`%2B`, `%2F`). Use `url_safe` alphabet instead.
5. **`decoderWithIgnore` is slightly slower** — it skips ignored characters during decode. Use only when needed.
