# std.ascii

7-bit ASCII character classification and manipulation. For Unicode text, use `std.unicode`.

## Quick Reference

```zig
const std = @import("std");
const ascii = std.ascii;
```

## Character Classification

All classification functions return `bool` and accept `u8`. Values > 127 return `false` (not ASCII).

```zig
ascii.isAlphanumeric('a')    // A-Z, a-z, 0-9
ascii.isAlphabetic('a')      // A-Z, a-z
ascii.isDigit('5')           // 0-9
ascii.isHex('F')             // A-F, a-f, 0-9
ascii.isUpper('A')           // A-Z
ascii.isLower('a')           // a-z
ascii.isWhitespace(' ')      // space, \t, \n, \r, \v, \f
ascii.isPrint('!')           // printable (not control)
ascii.isControl('\n')        // control chars (0x00-0x1F, 0x7F)
ascii.isAscii(c)             // c < 128
ascii.isSpace(' ')           // space only (not all whitespace)
ascii.isGraph('x')           // printable and visible (not space)
ascii.isPunct(',')           // punctuation (printable and not alphanumeric)
ascii.isBlank(' ')           // space or tab
ascii.isXDigit('f')          // hex digit (same as isHex)
```

## Case Conversion

### Single Character

```zig
ascii.toUpper('a')  // 'A' (no-op if already upper)
ascii.toLower('A')  // 'a' (no-op if already lower)
```

### String — To Buffer

```zig
var buf: [100]u8 = undefined;

const lower = ascii.lowerString(&buf, "HeLLo");  // "hello"
const upper = ascii.upperString(&buf, "HeLLo");  // "HELLO"
// Panics if buf is too small
```

### String — Allocating

```zig
const lower = try ascii.allocLowerString(allocator, "HeLLo");
defer allocator.free(lower);  // "hello"

const upper = try ascii.allocUpperString(allocator, "HeLLo");
defer allocator.free(upper);  // "HELLO"
```

## Case-Insensitive Comparison

```zig
// Equality
ascii.eqlIgnoreCase("Hello", "HELLO")  // true

// Prefix/suffix
ascii.startsWithIgnoreCase("Hello World", "hello")  // true
ascii.endsWithIgnoreCase("Hello World", "WORLD")    // true

// Search
ascii.indexOfIgnoreCase("Hello World", "world")     // ?usize = 6

// Lexicographic order (for sorting)
ascii.orderIgnoreCase("abc", "ABC")       // .eq
ascii.lessThanIgnoreCase("abc", "abd")    // true
```

## Constants

```zig
// Character set strings
ascii.lowercase  // "abcdefghijklmnopqrstuvwxyz"
ascii.uppercase  // "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ascii.letters    // concatenation of lowercase + uppercase
ascii.digits     // "0123456789"
ascii.hexdigits  // lowercase hex digits

// Whitespace array (for use with std.mem.trim)
ascii.whitespace  // [_]u8{ ' ', '\t', '\n', '\r', '\v', '\f' }
```

## Control Code Constants

```zig
const cc = std.ascii.control_code;

cc.nul   // 0x00  Null
cc.soh   // 0x01  Start of Heading
cc.stx   // 0x02  Start of Text
cc.etx   // 0x03  End of Text
cc.eot   // 0x04  End of Transmission
cc.enq   // 0x05  Enquiry
cc.ack   // 0x06  Acknowledge
cc.bel   // 0x07  Bell
cc.bs    // 0x08  Backspace
cc.ht    // 0x09  Horizontal Tab (\t)
cc.lf    // 0x0A  Line Feed (\n)
cc.vt    // 0x0B  Vertical Tab
cc.ff    // 0x0C  Form Feed
cc.cr    // 0x0D  Carriage Return (\r)
cc.so    // 0x0E  Shift Out
cc.si    // 0x0F  Shift In
cc.dle   // 0x10  Data Link Escape
cc.dc1   // 0x11  Device Control 1 (XON)
cc.dc2   // 0x12  Device Control 2
cc.dc3   // 0x13  Device Control 3 (XOFF)
cc.dc4   // 0x14  Device Control 4
cc.nak   // 0x15  Negative Acknowledge
cc.syn   // 0x16  Synchronous Idle
cc.etb   // 0x17  End of Transmission Block
cc.can   // 0x18  Cancel
cc.em    // 0x19  End of Medium
cc.sub   // 0x1A  Substitute
cc.esc   // 0x1B  Escape
cc.fs    // 0x1C  File Separator
cc.gs    // 0x1D  Group Separator
cc.rs    // 0x1E  Record Separator
cc.us    // 0x1F  Unit Separator
cc.del   // 0x7F  Delete

// Flow control aliases
cc.xon   // dc1 — Resume transmission
cc.xoff  // dc3 — Pause transmission
```

## Hex Escape Formatting

Format binary data with non-printable bytes escaped:

```zig
const data = "hello\x00world\xff!";

// Lowercase hex escapes
try stdout.print("{f}\n", .{ascii.hexEscape(data, .lower)});
// Output: hello\x00world\xff!

// Uppercase hex escapes
try stdout.print("{f}\n", .{ascii.hexEscape(data, .upper)});
// Output: hello\x00world\xFF!
```

## Common Patterns

### Trim Whitespace

```zig
const trimmed = std.mem.trim(u8, "  hello  ", &ascii.whitespace);
// "hello"
```

### Validate ASCII String

```zig
fn isAsciiString(s: []const u8) bool {
    for (s) |c| {
        if (!ascii.isAscii(c)) return false;
    }
    return true;
}
```

### Case-Insensitive Map Lookup

```zig
var buf: [64]u8 = undefined;
const normalized = ascii.lowerString(&buf, user_input);
if (map.get(normalized)) |value| { /* found */ }
```

### Count Words

```zig
fn countWords(text: []const u8) usize {
    var count: usize = 0;
    var in_word = false;
    for (text) |c| {
        if (ascii.isAlphanumeric(c)) {
            if (!in_word) {
                in_word = true;
                count += 1;
            }
        } else {
            in_word = false;
        }
    }
    return count;
}
```

### Hex Digit Value

```zig
fn hexValue(c: u8) ?u4 {
    return switch (ascii.toUpper(c)) {
        '0'...'9' => @truncate(c - '0'),
        'A'...'F' => @truncate(c - 'A' + 10),
        else => null,
    };
}
```

## Gotchas

1. **Not for Unicode** — all functions operate on `u8` and treat values > 127 as either `false` (classification) or pass-through (case conversion).
2. **`lowerString` / `upperString` assert buffer size** — they don't return errors; they panic if the output buffer is too small. Use `allocLowerString` for dynamic allocation.
3. **`isWhitespace` vs `isSpace`** — `isWhitespace` includes all six whitespace characters; `isSpace` matches only space (0x20).
4. **`hexEscape` uses `{f}` format specifier** — requires `{f}` in format string, not `{}`.
5. **`orderIgnoreCase` follows ASCII ordering** — `'Z' < 'a'` because uppercase letters come before lowercase in ASCII. Use this only for case-insensitive comparison, not locale-aware sorting.
