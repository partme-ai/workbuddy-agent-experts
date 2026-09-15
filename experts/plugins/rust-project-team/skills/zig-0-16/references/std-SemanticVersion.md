# std.SemanticVersion

Semantic version (SemVer 2.0) parsing, comparison, and formatting.

## Types

### Version

```zig
pub const Version = struct {
    major: usize,
    minor: usize,
    patch: usize,
    pre: ?[]const u8 = null,   // pre-release identifier
    build: ?[]const u8 = null,  // build metadata
};
```

### Range

```zig
pub const Range = struct {
    min: Version,
    max: Version,
};
```

## Functions

### Parse

```zig
const ver = try std.SemanticVersion.parse("1.2.3");
// ver.major == 1, ver.minor == 2, ver.patch == 3

const ver2 = try std.SemanticVersion.parse("2.0.0-alpha.1+build.2024");
// ver2.pre == "alpha.1", ver2.build == "build.2024"
```

### Order (Compare)

```zig
const a = try std.SemanticVersion.parse("1.0.0");
const b = try std.SemanticVersion.parse("2.0.0");
const order = a.order(b);
// order == .lt

switch (a.order(b)) {
    .lt => std.debug.print("a < b\n", .{}),
    .eq => std.debug.print("a == b\n", .{}),
    .gt => std.debug.print("a > b\n", .{}),
}
```

### Format

```zig
const ver = try std.SemanticVersion.parse("1.2.3");
var buf: [64]u8 = undefined;
var w: std.Io.Writer = .fixed(&buf);
try ver.format(&w);
const s = w.buffered();  // "1.2.3"
```

### Range Checking

```zig
const range = std.SemanticVersion.Range{
    .min = try std.SemanticVersion.parse("1.0.0"),
    .max = try std.SemanticVersion.parse("2.0.0"),
};

const ver = try std.SemanticVersion.parse("1.5.0");
const included = range.includesVersion(ver);   // true
const at_least = range.isAtLeast(ver);          // ?bool
```

## Parsing Errors

```zig
// Returns error.InvalidVersion if parsing fails
const ver = std.SemanticVersion.parse("not-a-version") catch |err| switch (err) {
    error.InvalidVersion => {
        std.debug.print("Invalid version string\n", .{});
        return;
    },
};
```

## Gotchas

1. **Pre-release precedence** — `1.0.0-alpha` < `1.0.0-alpha.1` < `1.0.0-alpha.beta` < `1.0.0-beta` < `1.0.0`.
2. **Build metadata** — `1.0.0+build1` and `1.0.0+build2` have the same precedence (build is ignored in comparison).
3. **`order()` follows SemVer 2.0** — numeric identifiers are compared numerically; alphanumeric are compared lexicographically.
4. **Null fields** — if `pre` or `build` are null, they're treated as absent (not empty string).
