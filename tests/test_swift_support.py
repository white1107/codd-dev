"""Tests for Swift language support in CoDD."""
import re
from pathlib import Path

import pytest

from codd.extractor import (
    _common_stdlib,
    _detect_code_patterns,
    _extract_imports,
    _extract_symbols,
    _file_to_module,
    _guess_test_target,
    _language_extensions,
)
from codd.parsing import BuildDepsExtractor, TestExtractor, TestInfo


# ── Symbol extraction ──────────────────────────────────────


class TestSwiftSymbols:
    def test_class(self):
        code = "class AppDelegate: UIResponder {"
        symbols = _extract_symbols(code, "Sources/App/AppDelegate.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "AppDelegate"
        assert symbols[0].kind == "class"

    def test_struct(self):
        code = "struct ContentView: View {"
        symbols = _extract_symbols(code, "Sources/App/ContentView.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "ContentView"

    def test_enum(self):
        code = "enum NetworkError: Error {"
        symbols = _extract_symbols(code, "Sources/Models/Error.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "NetworkError"

    def test_protocol(self):
        code = "protocol Repository {"
        symbols = _extract_symbols(code, "Sources/Protocols/Repository.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "Repository"

    def test_actor(self):
        code = "actor DataStore {"
        symbols = _extract_symbols(code, "Sources/Store/DataStore.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "DataStore"

    def test_func(self):
        code = "    func fetchData(id: Int) -> Data {"
        symbols = _extract_symbols(code, "Sources/Service.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "fetchData"
        assert symbols[0].kind == "function"

    def test_access_modifiers(self):
        code = """\
public class PublicModel {
private struct PrivateConfig {
open class OpenController {
"""
        symbols = _extract_symbols(code, "Sources/Models.swift", "swift")
        names = [s.name for s in symbols]
        assert "PublicModel" in names
        assert "PrivateConfig" in names
        assert "OpenController" in names

    def test_static_func(self):
        code = "    static func create(name: String) -> Self {"
        symbols = _extract_symbols(code, "Sources/Factory.swift", "swift")
        assert len(symbols) == 1
        assert symbols[0].name == "create"

    def test_multiple_symbols(self):
        code = """\
import Foundation

class UserService {
    func fetchUser(id: Int) -> User {
    }
    func deleteUser(id: Int) {
    }
}

struct User {
}
"""
        symbols = _extract_symbols(code, "Sources/UserService.swift", "swift")
        names = [s.name for s in symbols]
        assert "UserService" in names
        assert "fetchUser" in names
        assert "deleteUser" in names
        assert "User" in names


# ── Import extraction ──────────────────────────────────────


class TestSwiftImports:
    def test_simple_import(self, tmp_path):
        # Foundation/UIKit are in stdlib set, so they get filtered out
        code = "import Foundation\nimport UIKit\nimport Alamofire\n"
        internal, external = _extract_imports(
            code, "swift", tmp_path, tmp_path / "Sources", tmp_path / "Sources" / "App.swift"
        )
        # stdlib imports are removed by _common_stdlib
        assert "Foundation" not in external
        assert "UIKit" not in external
        # Third-party imports remain
        assert "Alamofire" in external
        assert len(internal) == 0

    def test_testable_import(self, tmp_path):
        code = "@testable import MyApp\n"
        # Create internal dir so it's recognized
        (tmp_path / "Sources" / "MyApp").mkdir(parents=True)
        internal, external = _extract_imports(
            code, "swift", tmp_path, tmp_path / "Sources", tmp_path / "Tests" / "MyAppTests.swift"
        )
        assert "MyApp" in internal

    def test_submodule_import(self, tmp_path):
        # Foundation is stdlib → filtered. Use a non-stdlib module instead.
        code = "import struct Alamofire.Session\n"
        internal, external = _extract_imports(
            code, "swift", tmp_path, tmp_path / "Sources", tmp_path / "Sources" / "Net.swift"
        )
        assert "Alamofire" in external

    def test_stdlib_filtered(self):
        stdlib = _common_stdlib("swift")
        assert "Foundation" in stdlib
        assert "UIKit" in stdlib
        assert "SwiftUI" in stdlib
        assert "CoreData" in stdlib
        assert "XCTest" in stdlib


# ── File to module mapping ─────────────────────────────────


class TestSwiftFileToModule:
    def test_simple(self, tmp_path):
        src = tmp_path / "Sources"
        src.mkdir()
        result = _file_to_module("Sources/App/AppDelegate.swift", tmp_path, src, "swift")
        assert result == "App"

    def test_root(self, tmp_path):
        src = tmp_path / "Sources"
        src.mkdir()
        result = _file_to_module("Sources/main.swift", tmp_path, src, "swift")
        assert result == "main.swift" or result == "root"  # single file in src root


# ── Language extensions ────────────────────────────────────


def test_swift_language_extensions():
    exts = _language_extensions("swift")
    assert ".swift" in exts


# ── Code pattern detection ─────────────────────────────────


class TestSwiftCodePatterns:
    def _make_mod(self):
        from codd.extractor import ModuleInfo
        return ModuleInfo(name="test")

    def test_swiftui_view(self):
        mod = self._make_mod()
        code = "import SwiftUI\nstruct ContentView: View {"
        _detect_code_patterns(mod, code, "swift")
        assert "swiftui_views" in mod.patterns

    def test_swiftdata_model(self):
        mod = self._make_mod()
        code = "@Model\nclass Item {"
        _detect_code_patterns(mod, code, "swift")
        assert "db_models" in mod.patterns

    def test_coredata_model(self):
        mod = self._make_mod()
        code = "class Entity: NSManagedObject {"
        _detect_code_patterns(mod, code, "swift")
        assert "db_models" in mod.patterns

    def test_observable(self):
        mod = self._make_mod()
        code = "@Observable\nclass ViewModel {"
        _detect_code_patterns(mod, code, "swift")
        assert "state_management" in mod.patterns


# ── Test file detection ────────────────────────────────────


class TestSwiftTestExtractor:
    def test_is_test_file(self):
        ext = TestExtractor("swift")
        assert ext._is_test_file("UserTests.swift") is True
        assert ext._is_test_file("UserTest.swift") is True
        assert ext._is_test_file("User.swift") is False
        assert ext._is_test_file("TestHelper.swift") is False

    def test_xctest_extraction(self):
        ext = TestExtractor("swift")
        code = """\
import XCTest
@testable import MyApp

class UserTests: XCTestCase {
    override func setUp() {
    }
    override func tearDown() {
    }
    func testCreate() {
    }
    func testDelete() {
    }
}
"""
        info = ext.extract_test_info(code, "Tests/UserTests.swift")
        assert "testCreate" in info.test_functions
        assert "testDelete" in info.test_functions
        assert "setUp" in info.fixtures
        assert "tearDown" in info.fixtures

    def test_swift_testing_extraction(self):
        ext = TestExtractor("swift")
        code = """\
import Testing
@testable import MyApp

struct UserTests {
    @Test func create() {
    }
    @Test func delete() {
    }
}
"""
        info = ext.extract_test_info(code, "Tests/UserTests.swift")
        assert "create" in info.test_functions
        assert "delete" in info.test_functions

    def test_detect_test_files(self, tmp_path):
        ext = TestExtractor("swift")
        (tmp_path / "FooTests.swift").write_text("test")
        (tmp_path / "Bar.swift").write_text("code")
        files = ext.detect_test_files(tmp_path)
        names = [f.name for f in files]
        assert "FooTests.swift" in names
        assert "Bar.swift" not in names


# ── Test target guessing ───────────────────────────────────


class TestSwiftGuessTarget:
    def test_tests_suffix(self):
        assert _guess_test_target("UserTests.swift", "swift") == "User"

    def test_test_suffix(self):
        assert _guess_test_target("UserTest.swift", "swift") == "User"

    def test_no_match(self):
        assert _guess_test_target("Helpers.swift", "swift") is None


# ── Build deps (Package.swift) ─────────────────────────────


# ── Type reference detection (cross-file) ──────────────────


class TestSwiftTypeReferences:
    def test_detects_cross_file_type_usage(self, tmp_path):
        """ContentView using SceneView() should create an edge."""
        from codd.scanner import _detect_swift_type_references
        from codd.graph import CEG

        src = tmp_path / "Sources"
        src.mkdir()
        (src / "ContentView.swift").write_text(
            "import SwiftUI\n"
            "struct ContentView: View {\n"
            "    var body: some View { SceneView() }\n"
            "}\n"
        )
        (src / "SceneView.swift").write_text(
            "import SwiftUI\n"
            "struct SceneView: View {\n"
            "    var body: some View { Text(\"hi\") }\n"
            "}\n"
        )

        scan_dir = tmp_path / "codd" / "scan"
        ceg = CEG(scan_dir)
        ceg.upsert_node("file:Sources/ContentView.swift", "file")
        ceg.upsert_node("file:Sources/SceneView.swift", "file")

        _detect_swift_type_references(ceg, tmp_path, src, [])

        # ContentView references SceneView → edge should exist
        found = any(
            e.get("source_id") == "file:Sources/ContentView.swift"
            and e.get("target_id") == "file:Sources/SceneView.swift"
            for e in ceg.edges
        )
        assert found

    def test_no_self_reference(self, tmp_path):
        """A file should not reference itself."""
        from codd.scanner import _detect_swift_type_references
        from codd.graph import CEG

        src = tmp_path / "Sources"
        src.mkdir()
        (src / "Foo.swift").write_text(
            "struct Foo {}\n"
            "let x = Foo()\n"
        )

        scan_dir = tmp_path / "codd" / "scan"
        ceg = CEG(scan_dir)
        ceg.upsert_node("file:Sources/Foo.swift", "file")

        _detect_swift_type_references(ceg, tmp_path, src, [])

        assert len(ceg.edges) == 0


# ── Build deps (Package.swift) ─────────────────────────────


class TestPackageSwiftDeps:
    def test_extract_deps(self):
        ext = BuildDepsExtractor()
        content = """\
let package = Package(
    name: "MyApp",
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.0.0"),
        .package(url: "https://github.com/realm/realm-swift.git", exact: "10.42.0"),
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.0.0"),
    ],
    targets: [
        .target(name: "MyApp", dependencies: ["Alamofire"]),
    ]
)
"""
        info = ext.extract_deps(content, "Package.swift", "Package.swift")
        assert "Alamofire" in info.runtime
        assert "realm-swift" in info.runtime
        assert "swift-composable-architecture" in info.runtime

    def test_empty_package(self):
        ext = BuildDepsExtractor()
        content = 'let package = Package(name: "Foo", dependencies: [])'
        info = ext.extract_deps(content, "Package.swift", "Package.swift")
        assert info.runtime == []
