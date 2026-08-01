# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-02

### ✨ New Features

- **`DataClassConfigBuilder` class** (`builder/dataclass_builder.py`) — Lightweight typed configuration builder using Python's stdlib `dataclasses`. Fills the gap between `RawConfigBuilder` (untyped dict) and `ConfigBuilder` (requires Pydantic). Inherits the full pipeline from `RawConfigBuilder` and adds a `build()` terminal method that returns a typed dataclass instance.
- **Basic type coercion** (`builder/dataclass_builder.py`) — Automatic coercion for common config-file scenarios where values are parsed as strings: `str` → `int` via `int()`, `str` → `float` via `float()`, `str` → `bool` via truthy/falsy string sets (`"true"`, `"1"`, `"yes"` → `True`; `"false"`, `"0"`, `"no"` → `False`).
- **Recursive nested dataclass instantiation** (`builder/dataclass_builder.py`) — When a field is annotated with a `@dataclass` type and the merged data contains a `dict`, the dict is recursively instantiated into the nested dataclass. Extra keys not present in the dataclass are handled via the `unknown_fields` option.

### 🔄 Changed

- **`builder.py` converted to `builder/` package** — Three builder classes now justify a package structure. `builder.py` has been split into `builder/__init__.py` (re-exports), `builder/_merge.py` (`_deep_merge`), `builder/raw_builder.py` (`RawConfigBuilder`), `builder/config_builder.py` (`ConfigBuilder`), and `builder/dataclass_builder.py` (`DataClassConfigBuilder`). All existing import paths (`from pyconfigre import ConfigBuilder`, `from pyconfigre.builder import _deep_merge`) continue to work unchanged.
- **`DataClassConfigBuilder` added to public API** (`__init__.py`) — Importable via `from pyconfigre import DataClassConfigBuilder` and included in `__all__`.
- **Version bumped to `0.3.0`** (`pyproject.toml`)

### 🧪 Tests

- Added `tests/unit/builder/test_dataclass_builder.py` — 31 tests across 6 test classes covering: basic instantiation (4 tests), file/env/multi-source loading (4 tests), type coercion for str→int/float/bool with valid and invalid inputs (9 tests), error handling for missing required fields, extra fields (`warn`/`ignore`/`forbid`), invalid configuration, and non-dataclass schemas (8 tests), pass-through behaviour (2 tests), fluent API chaining and inheritance verification (4 tests).
- Split `tests/unit/test_builder.py` into `tests/unit/builder/test_raw_builder.py`, `tests/unit/builder/test_config_builder.py`, and `tests/unit/builder/test_merge.py` (57 tests total) to mirror `src/pyconfigre/builder/` structure.
- Updated 2 mock paths in `tests/unit/builder/test_raw_builder.py` — `pyconfigre.builder.ConfigLoader` → `pyconfigre.builder.raw_builder.ConfigLoader` to reflect the folder conversion.
- All 177 unit tests pass. 99.78% coverage. `mypy` and `ruff` clean.
- **Integration test restructure** — Dissolved component-oriented `test_dataclass_loading.py` (21 tests) into workflow-oriented files: 12 validation/coercion tests → `test_validation.py` (`TestDataClassValidation`), 3 env coercion tests → `test_env_loading.py` (`TestDataClassENVCoercion`), 1 multi-source test → `test_multi_source_merging.py`. Removed 5 redundant tests that re-exercised inherited `RawConfigBuilder` pipeline behaviour already proven by existing workflow files. Replaced duplicated `_env` context manager in 4 files with shared `env_vars` from `conftest.py`. Added `SimpleConfigDC`, `DatabaseConfigDC`, `ComplexConfigDC` dataclass schemas to `tests/integration/conftest.py`.

---

## [0.2.0] - 2026-05-26

### ✨ New Features

- **`RawConfigbuilder` class** (`builder.py`) — Schema-free configuration pipeline. Provides the full loading, merging, and priority system without requiring a Pydantic model. All pipeline methods (`from_file`, `from_env`, `from_dict`, `set`, `peek`) live on this base class.
- **`build_dict()` terminal method** (`builder.py`) — Returns the final merged configuration as a plain dictionary. this is the terminal method for schema-free pipelines, analogous to `build()` on `ConfigBuilder`.

### 🔄 Changed

- **`ConfigBuilder` now extends `RawConfigBuilder`** (`builder.py`) — Two-class split: `RawConfigBuilder` is the base class with all pipeline logic; `ConfigBuilder(RawConfigBuilder, Generic[T])` adds typed Pydantic validation via `build()`. All existing `ConfigBuilder` usage is fully backwards-compatible.
- **Fluent method return types use `Self`** (`builder.py`) — Pipeline methods now return `typing_extensions.Self` instead of a string-literal fprward reference. This gives correct return types through inheritance: calling `.from_file()` on a `ConfigBuilder[AppConfig]` returns `ConfigBuilder[AppConfig]`, not `RawConfigBuilder`.
- **`RawConfigBuilder` added to public API** (`__init__.py`) — importable via `from pyconfigre import RawConfigBuilder` and included in `__all__`.
- **Version bumped to `0.2.0`** (`pyproject.toml`)

### 🧪 Tests

- Expanded `tests/unit/test_builder.py` — 57 tests total mirroring `src/pyconfigre/builder.py`: 39 tests covering `RawConfigBuilder` (parent) pipeline, exception handling and inheritance; 18 tests for `ConfigBuilder` (child) smoke tests with `build()`, Pydantic validation, integration, and the shared `_deep_merge` utility.

### 🤖 CI/CD

- **Renamed `ci.yaml` → `python-package.yml`** — follows GitHub Actions naming convention for package workflows
- **Centralised version constants** (`python-package.yml`) — `UV_VERSION` and `INTEGRATION_PYTHON_VERSION` moved to a top-level `env:` block; no more hardcoded values scattered across jobs
- **Adopted `uv sync` / `uv run`** (`python-package.yml`) — replaces manual venv activation across all jobs; `uv sync --extra dev` replaces the three-line `uv venv` + `source .venv/bin/activate` + `uv pip install` pattern
- **Enabled uv caching** (`python-package.yml`) — added `enable-cache: true` and `cache-dependency-glob: "pyproject.toml"` to all five `setup-uv` steps
- **Bumped actions to Node.js 24 compatible versions** (`python-package.yml`) — `checkout@v6`, `setup-uv@v7`, `setup-python@v6`, `upload-artifact@v6`, `codecov-action@v6`
- **Standardised Python installation pattern** (`python-package.yml`) — `setup-python` → `setup-uv` sequence applied consistently across all five jobs; `test` job previously used `python-version` input on `setup-uv` directly, now matches the other four jobs
- **Fixed issue auto-close for `feature → dev` merges** (`pr-lifecycle.yml`) — added explicit close call to `handle-closure` job; GitHub's native `Closes #N` keyword only fires on merges to the default branch (`main`); linked issues are now closed on any base branch merge
- **Added `main → dev` post-release sync workflow** (`sync-main-to-dev.yml`) — triggers on push to `main` and `workflow_dispatch`; opens a sync PR automatically; exits cleanly if branches are already in sync or a sync PR is already open
- **Added `validate-pr.yml`** — enforces two rules on every PR:
  - PR body must contain `Closes/Fixes/Resolves #N`
  - Head branch must start with a recognised prefix from `pr-labeling.json`
  - Posts a template comment on failure so the author knows exactly what to fix
  - Both checks always run before the job fails
  - `dev` branch exempt from the branch name check (release PRs)
  - `dev` branch exempt from the linked issue check (integration PRs)
  - Configured as a required status check on `dev` and `main`
- **Added `.githooks/post-checkout`** — warns immediately when a branch is created with an unrecognised name; cannot block (exit code ignored by git)
- **Added `.githooks/commit-msg`** — blocks commits on branches with unrecognised names; hard enforcement gate; skips `main`, `dev`, `HEAD`
- **Added `.githooks/templates/`** — message templates for both hooks (`commit-blocked.txt`, `checkout-warning.txt`)
- **Added `scripts/setup_hooks.py`** — cross-platform hook setup script; run with `uv run python scripts/setup_hooks.py`
- **Added descriptive YAML comment headers** to all five workflow files
- **Updated `CONTRIBUTING.md`** — added Git Hooks section with setup command, example output for both hooks, and Windows compatibility note; updated Development Setup to use `uv sync --extra dev`
- **Added `uv.lock`** — committed for reproducible dependency installs across all machines and CI runs
- **Updated `python-package.yml`** —
  - Updated to use `uv.lock` for caching and `--frozen` flag
  - Updated `cache-dependency-glob` from `pyproject.toml` to `uv.lock`
- **Added `.github/ISSUE_TEMPLATE/general.md`** — issue template for general issues
- **Added `.github/PULL_REQUEST_TEMPLATE.md`** — pre-fills PR description with the standard structure used across all PRs in the project
- **Added `pypi-publish.yml`** — automated PyPI publishing on GitHub release (`v*.*.*` tags only); uses OIDC Trusted Publishers (no API token); requires `pypi` GitHub Environment.

## [0.1.1] - 2026-03-26

### 🐛 Bug Fixes

- **`from_file` extension ordering** (`builder.py`) — Extension is now validated *before* checking file existence. Writing `.from_file("config.xyz")` before the file exists now raises `ValueError: Unsupported file format` immediately, not a misleading `ConfigNotFoundError` after the file is created.
- **`set()` error message** (`builder.py`) — Calling `set()` with a dot-notation path where an intermediate segment is already a scalar now raises `TypeError` with a message naming the full key path, the offending segment, its actual type, and a concrete resolution suggestion.
- **`ENVLoader` double-underscore nesting** (`loaders/env.py`) — Double underscores in environment variable names are now expanded into nested dicts: `MYAPP__DATABASE__HOST=localhost` → `{"database": {"host": "localhost"}}`. Single underscores remain part of the key name. Pass `nested=False` to opt out.
- **`ENVLoader` integer parsing** (`loaders/env.py`) — Integer values such as `"42"` were incorrectly parsed as `42.0` (float) because `float()` was attempted before `int()`. Parse order corrected.
- **`ConfigLoader` test isolation** (`loaders/manager.py`) — `ConfigLoader.reset()` restores the registries to their post-import state, preventing tests that register custom loaders from polluting subsequent tests.
- **Broken documentation examples** (`__init__.py`) — Module docstring examples corrected to use `from_file()` consistently. References to non-existent `from_yaml()` and `from_json()` methods removed.

### ✨ New Features

- **`ConfigBuilder.peek()`** (`builder.py`) — Returns a copy of the current assembled data without triggering Pydantic validation. Useful for inspecting merged state mid-chain. `get_raw_data()` retained as a deprecated alias that emits `DeprecationWarning`.
- **`from_env(nested=True)` parameter** (`builder.py`, `loaders/env.py`) — Controls whether double-underscore keys are expanded into nested dicts. Defaults to `True`.
- **`ConfigLoader.validate_extension()`** (`loaders/manager.py`) — Validates a file extension against registered loaders and returns the loader-type name. Extracted from `detect_and_load` for direct use.
- **`ConfigLoader.reset()`** (`loaders/manager.py`) — Restores registries to built-in state. Intended for test teardown after custom loader registration.

### 🔄 Changed

- **`_deep_merge` moved to module level** (`builder.py`) — Was an instance method that never used `self`. Now a module-level function importable by future sibling classes.
- **`ConfigBuilder._config_class` made private** (`builder.py`) — Attribute renamed from `config_class` to `_config_class`. It was never part of the documented public API. *Migration: change `builder.config_class` to `builder._config_class`.*
- **`from_env()` keyword-only parameters** (`builder.py`) — `lowercase`, `strip_prefix`, and `nested` are now keyword-only. *Migration: `from_env("P", True, False)` → `from_env("P", lowercase=True, strip_prefix=False)`.*
- **`get_raw_data()` emits `DeprecationWarning`** (`builder.py`) — Now warns on every call with `stacklevel=2`. Use `peek()` instead.
- **`list_loaders()` and `list_extensions()` return sorted results** (`loaders/manager.py`) — Deterministic output regardless of registration order.
- **`pyproject.toml` coverage config** — Now `--cov` targets to `src/pyconfigre` instead of bare `pyconfigre`;
- **`pyproject.toml` coverage config** — `*/__init__.py` now removed from `coverage.run.omit` which was hiding real code in `src/pyconfigre/__init__.py` from the report  and `tests/*` added to `coverage.run.omit` to exclude test code from coverage report.

### 🤖 CI/CD

- Added `pr-lifecycle.yml` — 3-job workflow managing PR labelling, issue sync, and closure handling
- Added `sync-labels.yml` — automated label sync triggered on config change or manual dispatch
- Added `.github/config/pr-labeling.json` for config-driven branch conventions
- Added `.github/config/labels.json` as single versioned source of truth for all labels
- Added `CONTRIBUTING.md`
- Updated `actions/checkout` to `@v5` across all workflows
- Fixed `test` job: add `-m "not integration"` filter — unit and integration tests now run in separate jobs with separate purposes
- Fixed `test` job: fix `continue-on-error: true` — was silently swallowing failures and reporting green CI on failing code
- Fixed `integration` job: migrate from ad-hoc script to `pytest -m integration` against the built wheel

### 🧪 Tests

- Restructured `tests/` into `tests/unit/` and `tests/integration/` — all existing tests moved to `tests/unit/` with no content changes; `conftest.py` stays at `tests/` root so fixtures are available to both layers
- Added 54 integration tests across 9 use-case files covering all formats (YAML, JSON, TOML, env), multi-source merging, optional files, validation, fluent API, and unsupported format handling
- Registered `integration` pytest mark in `pyproject.toml` — resolves `PytestUnknownMarkWarning` when `--strict-markers` is active
- Added `pragma: no cover` to `PackageNotFoundError` except block in `__init__.py` and four `DummyLoader`/`TempLoader` `__call__` bodies in `test_manager.py` — genuinely unreachable code removed from coverage report

---

## [0.1.0] - 2026-02-06

### 🎉 Initial Release

PyConfigre is a lightweight, type-safe configuration management library designed for modern Python applications. This initial release brings together multiple years of configuration management best practices into a simple, elegant API.

### ✨ Core Features Added

#### Multi-Format Configuration Loading
- **YAML support** via PyYAML for human-readable configuration files
- **JSON support** using Python's built-in `json` module
- **TOML support** via tomllib (Python 3.11+) or tomli (Python < 3.11)
- **Environment variable loading** with customizable prefix support
- **Dictionary-based configuration** for runtime overrides
- **Automatic format detection** based on file extensions

#### ConfigBuilder Class
- **Fluent API** for chainable, readable configuration building
  - `.from_file()` - Load from YAML, JSON, or TOML files
  - `.from_env()` - Load from environment variables with prefix
  - `.from_dict()` - Load from Python dictionaries
  - `.set()` - Set individual configuration values
  - `.build()` - Validate and build final configuration
- **Generic type support** (`ConfigBuilder[T]`) for proper type inference
- **Full type safety** with MyPy strict mode compliance
- **Method chaining** for elegant configuration composition

#### Robust Validation & Error Handling
- **Pydantic integration** for powerful, declarative validation
- **Custom exception hierarchy**:
  - `ConfigError` - Base exception for all configuration errors
  - `ConfigLoadError` - Errors during configuration file loading
  - `ConfigNotFoundError` - Configuration file not found
  - `ConfigValidationError` - Pydantic validation errors with detailed context
- **Detailed error messages** that help developers quickly identify and fix issues
- **Graceful fallbacks** for optional configuration files

#### Loader Infrastructure
- **Abstract `BaseConfigLoader`** for future extensibility
- **Environment variable loader** with prefix support and nested key handling
- **Format auto-detection** based on file extensions
- **Loader manager** for intelligent format detection and caching
- **Error recovery** with comprehensive exception handling

#### Type Safety & Developer Experience
- **Full type hints** throughout the entire codebase
- **Generic `ConfigBuilder[T]`** for type-safe configuration without casting
- **MyPy strict mode** compliance with zero type errors
- **Python 3.10+ syntax** including modern type union (`|`) syntax
- **IDE autocomplete support** for configuration fields

### 📊 Quality & Testing

#### Comprehensive Test Suite
- **105 tests** covering all core functionality
- **~98% code coverage** (only unavoidable tomli import error lines uncovered)
- **Test organization** matching source code structure
  - `tests/loaders/` - Individual loader testing
  - `tests/test_builder.py` - ConfigBuilder and fluent API testing
  - `tests/test_exceptions.py` - Exception handling and error cases

#### Type Checking & Linting
- **MyPy strict mode** - Zero type errors
- **Ruff** with comprehensive linting rules
- **Code formatting** with automatic style enforcement
- **Branch coverage** enabled for thorough testing

#### CI/CD Infrastructure
- **GitHub Actions workflow** for multi-version testing
- **Matrix strategy** testing Python 3.10, 3.11, 3.12, 3.13, and 3.14
- **Automated test reporting** with markdown and JSON outputs
- **Coverage tracking** with detailed reports per Python version
- **Artifact retention** for build verification

### 📚 Documentation

#### README & Examples
- **Comprehensive README** with quick start guide
- **Multiple usage patterns** demonstrating real-world scenarios
- **Best practices guide** for secure and maintainable configuration
- **Security guidelines** for handling sensitive data
- **Example scripts** in `scripts/` directory showing all features

#### Configuration Examples
- **Basic YAML loading** with type validation
- **Multiple source merging** with priority handling
- **Nested configuration structures** using Pydantic models
- **Environment variable overrides** with prefix support
- **Production-like scenarios** for API services and applications

#### Project Documentation
- **CHANGELOG** tracking all changes
- **Python version testing plan** with multi-version strategies
- **Inline code documentation** with docstrings on all public APIs
- **Type hints** serving as inline API documentation

### 🏗️ Project Structure

```
PyConfigre/
├── .github/                      # GitHub configuration
│   └── workflows/                # CI/CD workflows
├── scripts/                      # Integration test scripts
├── src/pyconfigre/                # Main package
│   ├── __init__.py               # Public API exports
│   ├── builder.py                # ConfigBuilder[T] class
│   ├── exceptions.py             # Custom exceptions
│   ├── py.typed                  # Type hints marker (PEP 561)
│   └── loaders/                  # Loader implementations
│       ├── __init__.py
│       ├── base.py               # BaseConfigLoader ABC
│       ├── manager.py            # LoaderManager
│       ├── env.py                # Environment variable loader
│       ├── json.py               # JSON file loader
│       ├── toml.py               # TOML file loader
│       └── yaml.py               # YAML file loader
├── tests/                        # Test suite (105 tests)
├── CHANGELOG.md                  # This file
├── LICENSE                       # MIT License
├── README.md                     # User documentation
├── pyproject.toml                # Project configuration
└── .gitignore                    # Ignore-list for version control

```

### 🧠 Design Philosophy

PyConfigre is built on several key principles:

1. **Simplicity over magic** – Explicit configuration loading beats implicit auto-discovery
2. **Type safety first** – Full type hints enable IDE support and catch errors early
3. **Standards compliance** – Follows PEP 440 (versioning) and PEP 621 (project metadata)
4. **Minimal dependencies** – Only Pydantic required; YAML and TOML are optional
5. **Fail fast** – Validation errors are raised at build time, not runtime
6. **Priority-based merging** – Clear, predictable configuration precedence

### 🔄 Configuration Priority

PyConfigre implements a simple, intuitive configuration priority system:

```
File → Environment Variables → Dict → Explicit .set() method
↑                                     ↑
Low                                   High
```

This matches how most systems expect configuration to work and makes it easy to understand which source will win in any given situation.

### 📦 Dependencies

**Core (required):**
- `pydantic >= 2.0.0` - Configuration validation and type checking
- `pyyaml >= 6.0` - YAML file support

**Optional:**
- `tomli >= 2.0.0` - TOML support (Python < 3.11; built-in for 3.11+)

**Development:**
- `pytest >= 9.0.0` - Testing framework
- `pytest-cov >= 7.0.0` - Coverage reporting
- `mypy >= 1.10.0` - Static type checking
- `ruff >= 0.4.0` - Linting and formatting

### ✅ Known Limitations

- **YAML features** - Limited to features supported by PyYAML
- **Circular references** - Not supported in configuration validation (expected for configs)
- **Very large files** - Performance not optimized for multi-hundred-MB configuration files
- **Real-time reloading** - Configuration is loaded once at startup (planned for future)

### 🎯 Version Management

- **Version**: 0.1.0 (Initial release)
- **Python compatibility**: 3.10, 3.11, 3.12, 3.13, 3.14
- **API stability**: This is an early release; minor breaking changes may occur before v1.0.0
- **Versioning**: Follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH)

### 🙏 Thanks

Special thanks to:
- The **Pydantic** team for an exceptional validation library
- The **PyYAML** and **tomli** maintainers for format support
- All contributors and early adopters providing feedback

---

## Comparison with Other Tools

If you're currently using alternative tools:
- **python-dotenv + manual merging** - PyConfigre provides cleaner API and type safety
- **configparser** - PyConfigre supports multiple formats with validation
- **hydra** - PyConfigre is simpler for most application needs
- **dynaconf** - PyConfigre has zero-configuration setup, no need for environment prefixes

Each has different strengths. Choose based on your project's specific needs.

---

[0.3.0]: https://github.com/aditya-barik/PyConfigre/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aditya-barik/PyConfigre/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/aditya-barik/PyConfigre/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/aditya-barik/PyConfigre/releases/tag/v0.1.0
