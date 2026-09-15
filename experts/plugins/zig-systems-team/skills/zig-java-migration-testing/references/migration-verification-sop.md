# Java-to-Zig Migration Verification SOP

## 1. Freeze evidence identity

Record Java SHA, Zig SHA, JDK/build tool, Zig version, target, optimization mode,
build options, test roots, asset roots, and every command before interpreting
results. Stale artifacts never prove the current target.

## 2. Whole-project module

Use directory `<project>-test`, import public production modules, and register:

```zig
const migration_tests = b.addTest(.{
    .root_module = b.createModule(.{
        .root_source_file = b.path("<project>-test/src/root.zig"),
        .target = target,
        .optimize = optimize,
    }),
});
const run_migration_tests = b.addRunArtifact(migration_tests);
const migration_step = b.step("migration-test", "Run complete Java/Zig parity suite");
migration_step.dependOn(&run_migration_tests.step);
```

Keep the directory out of production install artifacts and `build.zig.zon`
publication paths.

## 3. Source case records

Create one record per Java test method and per distinct parameterized/dynamic
case. Include target anchors, five preservation flags, disposition, result
parity, and retained case evidence. Disabled source tests remain blockers until
implemented and executed.

## 4. Source assets

Discover conventional Java `src/test/resources`, `test/resources`, and
`tests/resources` roots plus repository-specific fixture/script/corpus roots.
Copy every file without byte changes and record SHA-256.

## 5. Differential artifacts

Retain separately:

- raw Java output;
- raw Zig output;
- normalized Java output;
- normalized Zig output;
- comparison report;
- normalizer version and tests.

Normalize only documented nondeterminism such as temporary paths or timestamps
that are explicitly outside the contract. Do not normalize error category,
field presence, numeric precision, stable order, state, side effects, cleanup,
or security-relevant text.

## 6. Manifest example

Use [the template](../assets/source-test-parity.json). Completion requires:

- every source mapping has a complete disposition;
- every preservation flag is true;
- every target file and evidence artifact exists;
- every copied asset hash matches;
- Java, target, acceptance, and differential runs pass;
- differential `matched` equals the number of manifest cases;
- failed, skipped, mismatched, harness-failed, and not-run counts are zero.

## 7. Zig obligations

Run applicable allocator/leak, partial-failure cleanup, exact error, comptime,
optimization-mode, cross-target, ABI, concurrency, serialization, fuzz, load,
and real-host tests after source parity. Record them outside the source parity
numerator.

## 8. Honest conclusion

Report structural mapping, implementation, behavioral parity, host integration,
non-functional readiness, security, and rollback independently. Any incomplete
object ledger state overrides a green test report.
