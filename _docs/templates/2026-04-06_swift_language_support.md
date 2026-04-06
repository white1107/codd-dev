# Swift Language Support

## Background
- CoDD supported Python/TypeScript/JavaScript/Go/Java but not Swift/iOS projects
- User wanted to use CoDD for iOS development workflows
- Goal: regex-based MVP without tree-sitter dependency

## Design Intent
- Followed Go's implementation pattern (regex-only, no tree-sitter) as the closest reference
- Regex-first approach chosen over tree-sitter-swift to keep dependencies minimal and ship fast
- Comprehensive stdlib filter (50+ Apple frameworks) to avoid false positives in external dependency detection

## Implementation
- `codd/extractor.py`: Added Swift to 9 dispatch points — language detection, extensions, symbol extraction (class/struct/enum/protocol/actor/func with access modifiers), import parsing (`import Foo` / `@testable import` / `import struct Foo.Bar`), stdlib exclusion, code pattern detection (SwiftUI/SwiftData/CoreData/Observable), entry points, test target guessing
- `codd/scanner.py`: Added `.swift` to extension map, Swift import edge creation in CEG
- `codd/parsing.py`: Added `Package.swift` parsing to `BuildDepsExtractor`, Swift test detection (`*Tests.swift`/`*Test.swift`), XCTest + Swift Testing framework support, lifecycle fixture extraction
- `tests/test_swift_support.py`: 29 tests covering all features

## Side Effects & Notes
- **Known limitation**: Swift same-module type references produce 0 edges in `codd scan` because Swift doesn't require `import` within the same target. A type-reference scanner is needed (future work).
- `rstrip(".git")` bug caught during testing — strips characters not substrings. Fixed with `endswith` + slice.
- `codd init` defaults `source_dirs` to `src/` which doesn't match iOS project layouts (`Sources/`, app target name). Users must manually edit `codd.yaml`.
- Validated on real project (KhmerVocab-iOS): 13 Swift files detected, 0 edges (expected given limitation above).
- 5 pre-existing test failures in suite are unrelated (tree-sitter/synth).

## Related Files
- `codd/extractor.py`
- `codd/scanner.py`
- `codd/parsing.py`
- `tests/test_swift_support.py`
