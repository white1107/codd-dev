# CoDD Architecture Overview

## Language Processing Pipeline

```
codd scan
  → scanner.py: _scan_source_directory()
    → Walks files by extension per language
    → Creates file nodes in CEG (Coherence Evidence Graph)
    → Calls _extract_imports_basic() for edge creation
      → Uses extractor from parsing.py (TreeSitter preferred, Regex fallback)

extractor.py: extract_facts()
  → _detect_language() — auto-detect by file count
  → _discover_modules() — walk source dirs, extract symbols/imports per file
  → _map_tests_to_modules() — match test files to source modules
  → _detect_patterns() — framework/ORM/test-framework detection from manifests
```

## Extractor Priority
1. `TreeSitterExtractor` — if tree-sitter + language binding available
2. `RegexExtractor` — fallback for all languages
3. Specialized extractors: `SqlDdlExtractor`, `PrismaSchemaExtractor`

## Supported Languages (as of v1.5.0+swift)
| Language | Symbols | Imports | Call Graph | Build Deps |
|----------|---------|---------|------------|------------|
| Python | Tree-sitter + Regex | Yes | Tree-sitter | pyproject.toml |
| TypeScript | Tree-sitter + Regex | Yes | Tree-sitter | package.json |
| JavaScript | Tree-sitter + Regex | Yes | Tree-sitter | package.json |
| Go | Regex | Yes | No | go.mod |
| Java | Regex | No | No | pom.xml (detection only) |
| Swift | Regex | Yes | No | Package.swift |
| SQL | Tree-sitter | N/A | N/A | N/A |
| Prisma | Custom | N/A | N/A | N/A |

## Key Files
- `codd/extractor.py` — core extraction logic, framework detection
- `codd/scanner.py` — CEG graph construction from source scan
- `codd/parsing.py` — tree-sitter extractors, build deps, test extractors
- `codd/graph.py` — CEG data structure
- `codd/cli.py` — CLI entry points (init, scan, impact, etc.)

## Dev Environment
- `uv run pytest tests/` to run tests
- `uv tool install -e .` for global editable install
- Pre-existing test failures (5) are in tree-sitter/synth tests, unrelated to language support
