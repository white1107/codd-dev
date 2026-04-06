# Adding a New Language to CoDD

## Checklist (follow Go/Swift as reference)

### extractor.py
- [ ] `_detect_language()` — add file extension to `ext_map`
- [ ] `_language_extensions()` — add extension set
- [ ] `_file_to_module()` — add module mapping logic
- [ ] `_extract_symbols()` — add regex patterns for types and functions
- [ ] `_extract_imports()` — add import parsing
- [ ] `_common_stdlib()` — add stdlib exclusion set (if applicable)
- [ ] `_detect_code_patterns()` — add framework/pattern detection
- [ ] `_detect_entry_points()` — add common entry point filenames
- [ ] `_guess_test_target()` — add test→module name mapping
- [ ] `_detect_*_patterns()` — add build file framework detection (optional)

### scanner.py
- [ ] `_scan_source_directory()` — add to `extensions` dict
- [ ] `_extract_imports_basic()` — add CEG edge creation for the language

### parsing.py
- [ ] `TestExtractor.detect_test_files()` — add suffix set
- [ ] `TestExtractor.extract_test_info()` — add dispatch
- [ ] `TestExtractor._is_test_file()` — add test file naming convention
- [ ] `TestExtractor._extract_<lang>()` — add test function extraction
- [ ] `BuildDepsExtractor` — add manifest file support (optional)

### Tests
- [ ] Create `tests/test_<lang>_support.py` with coverage for all above

## Gotchas
- `_common_stdlib()` filters imports BEFORE they reach `external` set — test accordingly
- `rstrip(".git")` strips character-by-character, not the substring — use `endswith` + slice instead
- `codd init` defaults `source_dirs` to `src/` — users must manually fix for non-standard layouts
