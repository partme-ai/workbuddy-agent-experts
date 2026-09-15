# Illegal Behavior

Undefined behavior (UB) conditions in Zig. In **Debug** and **ReleaseSafe** modes these are caught at runtime. In **ReleaseFast** and **ReleaseSmall** they are unchecked — the program may silently produce wrong results or crash.

## Complete UB Conditions

### 1. Reaching Unreachable Code

```zig
unreachable;  // Triggered in safe modes → panic
// In release modes → undefined behavior
```

### 2. Index Out of Bounds

```zig
const slice = items[100];  // if len(items) <= 100
// Safe modes → panic with stack trace
// Release modes → UB (may read adjacent memory)
```

### 3. Cast Negative Number to Unsigned Integer

```zig
const x: i32 = -1;
const y: u32 = @intCast(x);  // panic in safe modes
// Use @bitCast or check sign first
```

### 4. Cast Truncates Data

```zig
const x: u32 = 0xFFFF;
const y: u16 = @intCast(x);  // OK - fits
const z: u8 = @intCast(x);   // panic if x > 255
```

### 5. Integer Overflow

```zig
const x: u8 = 200;
const y: u8 = 100;
const z = x + y;  // overflow in safe modes → panic
// Use wrapping operators: x +% y
// Or overflow-checking builtins: @addWithOverflow(x, y)
```

Default operators check overflow. Use explicit alternatives for wrapping:

```zig
// Wrapping operations (never panic)
const a = x +% y;    // wrapping add
const b = x -% y;    // wrapping sub
const c = x *% y;    // wrapping mul
const d = x <<% y;   // wrapping shift

// Overflow-detecting builtins
const result = @addWithOverflow(u8, x, y);
if (result[1] != 0) { /* overflow occurred */ }
```

### 6. Division by Zero

```zig
const x = a / b;  // runtime error if b == 0
const y = a % b;  // runtime error if b == 0
```

### 7. Remainder Division by Zero

Same as division by zero — `@rem(a, 0)` and `@mod(a, 0)` are UB.

### 8. Exact Division Remainder

```zig
// @divExact requires remainder to be zero
const x = @divExact(10, 3);  // panic: 10 / 3 != 0 remainder
```

### 9. Attempt to Unwrap Null

```zig
const maybe: ?u32 = null;
const val = maybe.?;  // panic → cannot unwrap null
```

### 10. Attempt to Unwrap Error

```zig
const result: anyerror!u32 = error.Foo;
const val = try result;  // returns error
const val2 = result catch unreachable;  // panic if result is error
const val3 = result.?;  // panic if result is error (using .? on error union)
```

### 11. Invalid Error Code

```zig
@errorFromInt(9999);  // if 9999 is not a valid error value → UB
```

### 12. Invalid Enum Cast

```zig
const E = enum { a, b };
const e: E = @enumFromInt(42);  // panic if 42 is not a valid tag
```

### 13. Invalid Error Set Cast

```zig
const Set1 = error{A};
const Set2 = error{B};
const e: Set2 = @as(Set1, error.A);  // error.A not in Set2 → runtime error
```

### 14. Incorrect Pointer Alignment

```zig
const bytes: [4]u8 = .{ 1, 2, 3, 4 };
const ptr = @as(*align(1) u32, @ptrCast(&bytes));
const val = ptr.*;  // UB if u32 alignment (4) > actual alignment (1)
```

### 15. Wrong Union Field Access

```zig
const U = union(enum) { a: u32, b: f32 };
var u = U{ .a = 42 };
const val = u.b;  // panic — accessing inactive field
```

### 16. Out of Bounds Float to Integer Cast

```zig
const f: f64 = 1e100;
const i: i32 = @intFromFloat(f);  // panic: 1e100 doesn't fit in i32
```

### 17. Pointer Cast Invalid Null

```zig
const ptr: ?*i32 = null;
const deref = ptr.?.*;  // panic: dereferencing null
```

### 18. Incorrect Sentinel Termination

```zig
const slice: [:0]const u8 = "hello";  // missing null terminator
// Reading past slice bounds expecting sentinel → UB
```

### 19. Slicing Past End

```zig
const slice = items[5..3];  // negative length → panic in safe modes
```

### 20. Mutable Reference While Immutable Reference Exists

Aliasing violation — using `*const` and `*` simultaneously for the same memory:

```zig
var x: u32 = 42;
const r1: *const u32 = &x;
const r2: *u32 = &x;
r2.* = 10;   // writing through r2 while r1 is alive → UB
_ = r1.*;
```

### 21. Invalid Memory After Free

```zig
const ptr = try allocator.create(u32);
allocator.destroy(ptr);
ptr.* = 42;  // use-after-free → UB
```

### 22. Invalid Memory After Reallocation

```zig
const slice = try allocator.alloc(u32, 10);
const new_slice = try allocator.realloc(slice, 20);
// slice is now invalid — use new_slice instead
slice[0] = 42;  // UB: using old pointer after realloc
```

## Safe Mode Detection

```zig
// Check if safety is enabled at compile time
if (@import("builtin").mode == .Debug or @import("builtin").mode == .ReleaseSafe) {
    // Safety checks are active
}

// Or use @setRuntimeSafety to override
@setRuntimeSafety(false);  // disable safety in this scope
@setRuntimeSafety(true);   // re-enable safety
```

## Gotchas

1. **UB in release modes is silent** — your program may produce wrong results without crashing. Always test in Debug/ReleaseSafe.
2. **`unreachable` is the most dangerous UB** — in ReleaseFast, reaching `unreachable` can cause any behavior. Use it only when you can prove the path is impossible.
3. **Integer overflow is UB** — use `+%` for wrapping or `@addWithOverflow` for checked arithmetic.
4. **Safety checks have performance cost** — in hot loops, use `@setRuntimeSafety(false)` for the inner loop, then re-enable.
5. **`@setRuntimeSafety` is scope-local** — it affects the current block only, not the entire function.
