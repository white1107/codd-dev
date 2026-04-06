# Swift Language Support in CoDD

## Status
- MVP (regex-based) implemented as of 2026-04-06
- Call graph / type reference detection NOT yet implemented (see known limitation below)

## Implementation Locations
- `codd/extractor.py` — symbol extraction, import parsing, stdlib list, code pattern detection, entry points
- `codd/scanner.py` — `.swift` extension registration, CEG edge creation
- `codd/parsing.py` — TestExtractor (XCTest + Swift Testing), BuildDepsExtractor (Package.swift), test file detection
- `tests/test_swift_support.py` — 29 tests covering all Swift features

## Key Design Decisions
- Swift uses regex-only extraction (no tree-sitter-swift binding yet)
- Go language support was used as the reference pattern for adding Swift
- Swift stdlib filter includes 50+ Apple frameworks to avoid false external deps

## Known Limitation: Same-Module References
Swift files in the same target can reference each other without `import`. This means `codd scan` on a single-target iOS app produces **0 edges** between files. A type-reference scanner is needed to detect `NavigationLink(destination: FooView())` style dependencies. This is tracked as a future enhancement.

## Testing
```bash
uv run pytest tests/test_swift_support.py -v
```
All 29 tests should pass. The 5 pre-existing failures in the full suite are unrelated (tree-sitter/synth template tests).
