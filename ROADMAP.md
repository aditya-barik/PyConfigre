# PyConfigre — Development Roadmap

- Repository: https://github.com/aditya-barik/PyConfigre
- Package identity: A composable configuration assembly pipeline for Python. Load from any source, merge with intelligent priority, validate with Pydantic — or consume as a plain dict. Built for modern Python teams who want explicit, readable, testable configuration code.

## Release Timeline
```
    ●        ●        ●        ●        ◌        ◌        ◌        ◌
    │        │        │        │        │        │        │        │
────●────────●────────●────────●────────◌────────◌────────◌────────◌────
    │        │        │        │        │        │        │        │
  v0.1.0   v0.1.1   v0.2.0   v0.3.0   v0.3.1   v0.4.0   v0.5.0   v1.0.0
  shipped  shipped  shipped  shipped  current  planned  planned  target
  Feb 2026 Mar 2026 May 2026 Aug 2026
```

**Legend:** `●` shipped · `◌` planned · `current` = active development

## v0.1.0 — Initial Release ✅

Initial public release. Multi-format loading (YAML, JSON, TOML, env, dict), fluent ConfigBuilder API, Pydantic validation, full type safety, 98% test coverage across Python 3.10–3.14.

→ [Release Notes](https://github.com/aditya-barik/PyConfigre/releases/tag/v0.1.0) · [CHANGELOG](https://github.com/aditya-barik/PyConfigre/blob/main/CHANGELOG.md#010---2026-02-06)

## v0.1.1 — Correctness Fixes, Test Restructure & Automation ✅

Resolved six correctness bugs in the Python package, introduced the full GitHub automation infrastructure, and established a proper two-layer test architecture.

**Python fixes:** `from_file` extension ordering, `set()` error messages, `ENVLoader` double-underscore nesting, integer parse order, `ConfigLoader.reset()` for test isolation, `peek()` added with `get_raw_data()` as deprecated alias.

**Integration Test Suite + Test Restructure:** Established a proper two-layer test architecture that separates unit tests (fast, mock-heavy, all Python versions) from integration tests (end-to-end, real files, built wheel). Previously, tests lived in a flat `tests/` root with no separation between unit and integration concerns.

Restructured into `tests/unit/` and `tests/integration/`, with 54 new integration tests across 9 use-case files covering every format, every source combination, and every edge case in the public API. Fixed three CI issues uncovered during the restructure (e.g., removing `continue-on-error: true` which was silently hiding failures).

```
tests/
├── conftest.py            — shared unit fixtures
├── unit/                  — existing tests, moved (no content changes)
│   ├── test_builder.py
│   ├── test_exceptions.py
│   └── loaders/
│       └── test_*.py
└── integration/           — new (54 tests, 9 files)
    ├── conftest.py        — shared schemas and cfg_dir fixture
    ├── test_yaml_loading.py
    ├── test_json_loading.py
    ├── test_toml_loading.py
    ├── test_env_loading.py
    ├── test_multi_source_merging.py
    ├── test_optional_files.py
    ├── test_unsupported_formats.py
    ├── test_validation.py
    └── test_fluent_api.py
```

**GitHub automation:** `pr-lifecycle.yml`, `sync-labels.yml`, `.github/config/` structure, `CONTRIBUTING.md`, `WORKFLOW_ENFORCEMENT.md`.

→ [Release Notes](https://github.com/aditya-barik/PyConfigre/releases/tag/v0.1.1) · [CHANGELOG](https://github.com/aditya-barik/PyConfigre/blob/main/CHANGELOG.md#011---2026-03-26)

## CI Infrastructure Modernisation (Shipped; No Release) ✅

Modernised the CI pipeline to use uv to its full potential, enforced branch and PR conventions at the GitHub level, and provided local tooling. Shipped directly to repository infrastructure without a dedicated Python package release.

### CI Pipeline Rewrite:
- `ci.yaml` → `python-package.yml` - Full `uv sync` adoption, `uv run` for all commands, and caching enabled.

- `enable-caching: true` on all setup-uv steps — package cache persists between runs, faster CI.

- `UV_VERSION`, `PYTHON_VERSIONS`, `INTEGRATION_PYTHON_VERSION` defined once in the top-level env: block.

- Integration jobs now run `pytest -m integration` against the built wheel on Python 3.10.

### Automated Issue & Branch Management

- **Auto Issue Closing:** Added workflows to automatically close linked issues when a PR is merged into its base branch (ensuring it works even if the base branch is not `main`).

- **Post-Release Sync:** Implemented a workflow that automatically performs a `main` to `dev` merge after every release to keep the development branch perfectly synced.

### PR Validation Workflow & Git Hooks

Blocks PRs at the CI level if they are missing a linked issue or use a non-standard branch name. Reads branch prefixes directly from `.github/config/pr-labeling.json`. A local git hook (`.githooks/commit-msg`) catches branch naming issues before they reach GitHub.

## v0.2.0 — RawConfigBuilder + build_dict() (Shipped & Released on PyPI) ✅

**Goal:** Make the full configuration pipeline available without requiring a Pydantic schema.

**Problem:** `ConfigBuilder` is `Generic[T]` where `T` is bound to `BaseModel`. The entire pipeline — loading, format detection, merging, priority — is useful without Pydantic, but `ConfigBuilder(dict)` is a type error and `build_dict()` does not exist. The current design makes schema-less usage inaccessible.

**Solution:** Two-class split. `RawConfigBuilder` is the pure pipeline with no schema requirement. `ConfigBuilder` extends it and adds `Generic[T]` + `build()`.

### Architecture

```python
class RawConfigBuilder:
    """The pure pipeline — loading, merging, priority. No schema required."""

    def from_file(path, optional=False) -> "RawConfigBuilder": ...
    def from_env(prefix="", *, lowercase=True, strip_prefix=True, nested=True) -> "RawConfigBuilder": ...
    def from_dict(data) -> "RawConfigBuilder": ...
    def set(key, value) -> "RawConfigBuilder": ...
    def peek() -> dict[str, Any]: ...        # non-terminal — inspect mid-chain
    def build_dict() -> dict[str, Any]: ...  # terminal — returns raw merged dict


class ConfigBuilder(RawConfigBuilder, Generic[T]):
    """Extends the pipeline with typed Pydantic validation."""

    def __init__(self, schema: type[T]) -> None: ...
    def build() -> T: ...  # terminal — validates and returns Pydantic model

    # inherits everything from RawConfigBuilder
```

### Key design decisions

- `RawConfigBuilder` is the base — `ConfigBuilder` extends it
- `_deep_merge` (module-level since v0.1.1) shared by both without coupling
- Both classes in `builder.py` until v0.3.0 triggers folder conversion (three builder classes justify the package split)

### New public API

```python
# Schema-less — no Pydantic needed
from pyconfigre import RawConfigBuilder

raw = (
    RawConfigBuilder()
    .from_file("config.yaml")
    .from_env("MYAPP__")
    .build_dict()           # returns plain dict
)

# Typed — existing usage unchanged
from pyconfigre import ConfigBuilder

config = (
    ConfigBuilder(AppConfig)
    .from_file("config.yaml")
    .from_env("MYAPP_")
    .build()                # returns AppConfig instance
)
```

### File structure at v0.2.0

```
pyconfigre/
├── __init__.py       ← add RawConfigBuilder to __all__
├── builder.py        ← RawConfigBuilder + ConfigBuilder (same file, still flat)
├── exceptions.py
└── loaders/
    └── ...           ← unchanged
```

### Tests to add (`tests/unit/test_raw_builder.py`)

- `test_build_dict_returns_plain_dict`
- `test_build_dict_with_file_source`
- `test_build_dict_with_env_source`
- `test_build_dict_with_multiple_sources_priority`
- `test_raw_builder_peek_works`
- `test_raw_builder_set_works`
- `test_config_builder_still_inherits_all_pipeline_methods`
- `test_deep_merge_shared_between_both_classes`

## v0.3.0 — DataClassConfigBuilder + Folder Conversion ✅

**Goal:** Provide a lightweight typed configuration builder using Python's stdlib `dataclasses` — no Pydantic dependency required. Also converts `builder.py` into a `builder/` package now that three builder classes exist.

**Problem:** `ConfigBuilder` requires Pydantic, which is heavy for simple projects. `RawConfigBuilder` returns a plain dict with no type safety — there is no middle ground for projects that want typed attribute access without a validation framework.

### Architecture

```python
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"


@dataclass
class AppConfig:
    app_name: str = "my_app"
    debug: bool = False
    port: int = 8080
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
```

```python
class DataClassConfigBuilder(RawConfigBuilder, Generic[T]):
    """Extends the pipeline with Python dataclass instantiation."""

    def __init__(self, schema: type[T]) -> None: ...
    def build() -> T: ...  # terminal — instantiates dataclass from merged dict

    # inherits everything from RawConfigBuilder
```

### Three-tier builder hierarchy

| Builder | Schema | Output | Dependency |
|---------|--------|--------|------------|
| `RawConfigBuilder` | None | `dict[str, Any]` | stdlib only |
| `DataClassConfigBuilder` | `@dataclass` | dataclass instance | stdlib only |
| `ConfigBuilder` | `BaseModel` | Pydantic model | `pydantic` |

### New public API

```python
from pyconfigre import DataClassConfigBuilder

dataclass_config = (
    DataClassConfigBuilder(AppConfig)
    .from_file("config.yaml")
    .from_env("MYAPP_")
    .set("debug", True)  # mid-chain override
    .build()  # → AppConfig(app_name="my_app", debug=True, port=8080, database=DatabaseConfig(...))
)

# Attribute access — typed, IDE-friendly
print(dataclass_config.database.host)  # "localhost"
print(dataclass_config.port)           # 8080
```

### Type coercion strategy

Basic coercion for common cases (config files often parse everything as strings):

| Source type | Target type | Coercion logic |
|-------------|-------------|----------------|
| `str` | `int` | `int(value)` |
| `str` | `float` | `float(value)` |
| `str` | `bool` | `{"true", "1", "yes"}` → `True`, `{"false", "0", "no"}` → `False` |
| `dict`| nasted `@dataclass` | recursive instantiation |
| other | other | pass-through (let Python raise `TypeError`) |

### Folder conversion

Three builder classes justify converting `builder.py` into a `builder/` package:

```
pyconfigre/
├── __init__.py               ← add DataClassConfigBuilder to __all__
├── builder/
│   ├── __init__.py           ← re-exports all three builders
│   ├── raw_builder.py        ← RawConfigBuilder
│   ├── dataclass_builder.py  ← DataClassConfigBuilder (new)
│   ├── config_builder.py     ← ConfigBuilder
│   └── _merge.py             ← _deep_merge (extracted)
├── exceptions.py
└── loaders/
    └── ...                   ← unchanged
```

### Tests

- 31 new unit tests in `tests/unit/builder/test_dataclass_builder.py` across 6 test classes
- 16 integration tests distributed across existing workflow files:
  - 12 validation/coercion tests → `test_validation.py` (`TestDataClassValidation`)
  - 3 env coercion tests → `test_env_loading.py` (`TestDataClassENVCoercion`)
  - 1 multi-source test → `test_multi_source_merging.py`
- Dissolved `tests/integration/test_dataclass_loading.py` (21 tests) by moving 16 tests to workflow files and removing 5 redundant tests that re-exercised inherited `RawConfigBuilder` pipeline behaviour
- Replaced duplicated `_env` context manager in 4 integration test files with shared `env_vars` from `conftest.py`
- Added `SimpleConfigDC`, `DatabaseConfigDC`, `ComplexConfigDC` schemas to `tests/integration/conftest.py`
- Total: 177 unit tests + 70 integration tests = 247 tests, 99.78% coverage

## v0.3.1 — Correctness Fixes 📋 Current

**Goal:** Fix all bugs and inconsistencies found during the v0.3.0 code review. Pure fixes — no new features, no API changes. All existing tests must continue to pass; new tests are added only to cover the fixed behaviour.

### Fix 3.1.1 — `peek()` / `build_dict()` shallow copy → deepcopy

**Bug:** Both methods use `dict(self._data)` which is a shallow copy. Nested dict values share references with the builder's internal state:

```python
d = builder.peek()
d["server"]["port"] = 9999  # mutates builder._data["server"]["port"]!
```

**Fix:** `import copy; return copy.deepcopy(self._data)` in both `peek()` and `build_dict()`.

**File:** `builder/raw_builder.py` (lines 312, 334)

### Fix 3.1.2 — Wrong package name in TOML error message

**Bug:** `loaders/toml.py:59` says `pip install pyconfig[toml]` — wrong package name.

**Fix:** Change to `pip install pyconfigre[toml]`.

### Fix 3.1.3 — Wrong module name in `exceptions.py` docstring

**Bug:** `exceptions.py:1` says `"""Exception classes for pyconfig."""`

**Fix:** Change to `"""Exception classes for pyconfigre."""`

### Fix 3.1.4 — Wrong exception in `_check_file_exists` docstring

**Bug:** `loaders/base.py:88` Raises section says `ConfigLoadError`, but the method raises `ConfigNotFoundError`.

**Fix:** Change docstring to `ConfigNotFoundError`.

### Fix 3.1.5 — `RawConfigBuilder` docstring typo

**Bug:** `builder/raw_builder.py:36` says `Schmea-less usage::`.

**Fix:** Change to `Schema-less usage::`.

### Fix 3.1.6 — Missing `super().__init__()` calls

**Bug:** `ConfigBuilder.__init__` and `DataClassConfigBuilder.__init__` both set `self._data = {}` directly instead of calling `super().__init__()`. If `RawConfigBuilder.__init__` changes in the future, the subclasses will silently diverge.

**Fix:** Call `super().__init__()` and remove the redundant `self._data = {}` line in both `config_builder.py` and `dataclass_builder.py`.

### Fix 3.1.7 — Declare `typing_extensions` as explicit dependency

**Bug:** `raw_builder.py` imports `from typing_extensions import Self`, but `typing_extensions` is not in `pyproject.toml` dependencies. It works because Pydantic pulls it in transitively — but if Pydantic becomes optional in v0.4.0, `RawConfigBuilder` and `DataClassConfigBuilder` will break.

**Fix:** Add `typing_extensions>=4.0` to `[project] dependencies`.

### Fix 3.1.8 — Loader exception handling silently swallows `ConfigNotFoundError`

**Bug:** In `json.py`, `yaml.py`, and `toml.py`, the pattern `except ConfigLoadError: raise` does not catch `ConfigNotFoundError` (a sibling, not subclass of `ConfigLoadError`). The `ConfigNotFoundError` from `_check_file_exists()` falls through to `except Exception` and gets re-wrapped as `ConfigLoadError`, losing the original exception type.

**Fix:** Change to `except (ConfigLoadError, ConfigNotFoundError): raise` in all three loaders.

### Fix 3.1.9 — Boolean coercion inconsistency

**Bug:** `ENVLoader._parse_value` recognises `"on"` and `"off"` as booleans, but `dataclass_builder._coerce_value` does not. A user setting `MY_DEBUG=on` gets `True` from env loading, but `debug: "on"` from a YAML file through `DataClassConfigBuilder` fails to coerce.

**Fix:** Add `"on"` to `_TRUTHY` and `"off"` to `_FALSY` in `dataclass_builder.py`.

### Fix 3.1.10 — `_instantiate_dataclass` type guard inconsistency

**Bug:** Line 315 of `dataclass_builder.py` uses `isinstance(field_type, type)` while lines 310–312 use `_is_concrete_type(field_type)`. On Python 3.10, parameterized generics like `list[str]` pass `isinstance(type)` but fail `_is_concrete_type()`. Not a runtime crash (because `_coerce_value` has its own guard), but inconsistent and fragile.

**Fix:** Change line 315 to `elif _is_concrete_type(field_type):`.

### Fix 3.1.11 — CI workflow action version inconsistencies

**Bug:** `pr-lifecycle.yml` (lines 50, 91) and `sync-labels.yml` (line 36) use `actions/checkout@v5` while all other workflows use `@v6`.

**Fix:** Bump to `actions/checkout@v6`.

### Fix 3.1.12 — Missing `tests/unit/__init__.py`

**Bug:** Every other test directory has an `__init__.py` (`tests/`, `tests/integration/`, `tests/unit/builder/`, `tests/unit/loaders/`) except `tests/unit/`.

**Fix:** Add empty `tests/unit/__init__.py`.

### Fix 3.1.13 — `pyproject.toml` setuptools include pattern too broad

**Bug:** `[tool.setuptools.packages.find]` has `include = ["pyconfig*"]` which would also match an unrelated `pyconfig` package if one existed in `src/`.

**Fix:** Change to `include = ["pyconfigre*"]`.

### Fix 3.1.14 — CHANGELOG v0.2.0 typos

**Bug:** Three cosmetic typos in the v0.2.0 changelog:
- `RawConfigbuilder` → `RawConfigBuilder` (line 37)
- `this is the terminal` → `This is the terminal` (line 38)
- `fprward reference` → `forward reference` (line 42)

**Fix:** Correct all three.

### Tests

- Add regression test for nested-dict mutation through `peek()` (the existing test only checks top-level mutation)
- Add test for `"on"` / `"off"` bool coercion in `DataClassConfigBuilder`
- Verify `ConfigNotFoundError` propagates through loaders without re-wrapping

## v0.4.0 — Builder Feature Parity + New Capabilities 📋 Planned

**Goal:** Bring feature parity across all three builders and make Pydantic an optional dependency. Also ships the `from_env_layer()` convenience method.

### Feature 4.1 — `unknown_fields` parameter on `RawConfigBuilder` and `ConfigBuilder`

**Problem:** Only `DataClassConfigBuilder` supports `unknown_fields`. `RawConfigBuilder` silently accepts everything (fine for dicts), but `ConfigBuilder` users have no pre-build way to catch unexpected keys — they rely on Pydantic's `model_config` which is schema-side, not builder-side.

**Solution:** Add `unknown_fields` parameter to `RawConfigBuilder.__init__()` and `ConfigBuilder.__init__()` with the same `"ignore"` / `"warn"` / `"forbid"` modes. For `RawConfigBuilder`, validation happens at `build_dict()` time against a provided key set; for `ConfigBuilder`, validation happens at `build()` time against the Pydantic model fields.

### Feature 4.2 — `missing_fields` handling across all builders

**Problem:** Missing required fields currently raise different exceptions depending on the builder (`ValidationError` for Pydantic, `TypeError` for dataclasses, nothing for raw). There is no unified pre-build check.

**Solution:** Add `missing_fields` parameter (`"raise"` / `"warn"` / `"ignore"`) that checks for required fields before delegating to the schema validator.

### Feature 4.3 — Make Pydantic an optional dependency (`pyconfigre[pydantic]`)

**Problem:** `pydantic>=2.0.0` is a hard dependency in `pyproject.toml`, but `RawConfigBuilder` and `DataClassConfigBuilder` do not use Pydantic at all. Projects that only need dataclass or dict-based config carry an unnecessary heavy dependency.

**Solution:**
- Move `pydantic>=2.0.0` from `[project] dependencies` to `[project.optional-dependencies] pydantic`
- Guard `from pydantic import ...` in `config_builder.py` with a try/except `ImportError`
- Raise a clear `ImportError` at `ConfigBuilder.__init__()` if Pydantic is not installed
- Update `[project.optional-dependencies] all` to include `pydantic`
- Core dependencies become: `pyyaml>=6.0`, `typing_extensions>=4.0` only

### Feature 4.4 — `from_env_layer()`

**Problem:** The base → {env} → local layering pattern is written manually in every real project. It should be a single method call.

```python
# Today — every project writes this manually
env = os.getenv("ENV", "development")
config = (
    ConfigBuilder(AppConfig)
    .from_file("config/base.yaml", optional=True)
    .from_file(f"config/{env}.yaml", optional=True)
    .from_file("config/local.yaml", optional=True)
    .from_env("MYAPP_")
    .build()
)

# With from_env_layer()
config = (
    ConfigBuilder(AppConfig)
    .from_env_layer("config/", env_var="ENV", default="development")
    .from_env("MYAPP_")
    .build()
)
```

**Implementation:**

```python
def from_env_layer(
    self,
    directory: str | Path,
    *,
    env_var: str = "ENV",
    default: str = "development",
    base_name: str = "base",
    local_name: str = "local",
    extension: str = ".yaml",
) -> "RawConfigBuilder":
    directory = Path(directory)
    env_value = os.getenv(env_var, default)
    return (
        self.from_file(directory / f"{base_name}{extension}", optional=True)
        .from_file(directory / f"{env_value}{extension}", optional=True)
        .from_file(directory / f"{local_name}{extension}", optional=True)
    )
```

**Tests to add:** 8 tests covering base file, env-specific file, missing files skipped, local override priority, env var respected, custom base name, custom extension, default env value.

## v0.5.0 — New Pipeline Features 📋 Planned

**Goal:** Ship the features that make PyConfigre meaningfully differentiated from `pydantic-settings` and `dynaconf`.

### Feature 5.1 — Schema Inference (`infer_schema()`)

**Problem:** Writing a Pydantic model for a 50-key nested config file from scratch is the biggest adoption friction point for large existing projects.

**Solution:** Generate a Pydantic model skeleton from a loaded dict. Developers start with 90% of their schema and refine from there.

```python
raw = RawConfigBuilder().from_file("complex.yaml").build_dict()
schema_code = RawConfigBuilder.infer_schema(raw, name="AppConfig")
print(schema_code)  # → valid Python with nested BaseModel classes
```

**Type inference rules:**

| Python value | Inferred type |
|--------------|---------------|
| `True` / `False` | `bool` |
| `42` | `int` |
| `3.14` | `float` |
| `"hello"` | `str` |
| `[1, 2, 3]` | `list[int]` (element type from first item) |
| `None` | `Any` |
| `{"host": "x"}` | new nested BaseModel subclass |

**Tests to add:** 8 tests covering flat dict, nested subclass creation, bool-before-int ordering, None → Optional, list element inference, valid Python output (exec assertion), custom name, write-to-file.

### Feature 5.2 — Directory Loading (`from_directory()`)

**Problem:** Large projects organise configs as a folder of files. There is no way to load this structure into a single accessible namespace.

**Solution:** Load all supported files from a directory into a single namespace.

```python
cfg = load_directory("config/")
cfg.env.dev["host"]  # attribute access
cfg["env"]["dev"]["host"]  # subscript access
```

**New module:** `pyconfigre/directory.py` — `ConfigNamespace` + `load_directory()`.

**Tests to add:** 14+ tests covering all access patterns, missing root, non-directory path, unknown extensions (silent skip and explicit raise), `to_dict()` round-trip, read-only enforcement, `recursive=False`, hidden file skipping, and pipeline integration.

### Feature 5.3 — Conditional Loading (`when=` parameter)

**Problem:** Conditional source application today breaks the fluent chain with if blocks.

```python
# With conditions — stays fluent
config = (
    ConfigBuilder(AppConfig)
    .from_file("base.yaml")
    .from_file("dev.yaml", when=env_is("ENV", "dev"))
    .from_file("prod.yaml", when=env_is("ENV", "prod"))
    .from_env("MYAPP_")
    .build()
)
```

**Condition forms:** callable, 2-tuple `("ENV", "dev")`, 3-tuple with operator (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`), `{"all": [...]}` / `{"any": [...]}` sets, and helpers `env_is()`, `env_in()`, `when_all()`, `when_any()`.

**New module:** `pyconfigre/conditions.py`.

**Tests to add:** 20+ tests covering all condition forms, all operators, `all`/`any` logic, error cases, helpers, and mixin integration.

**File structure at v0.5.0:**

```
pyconfigre/
├── __init__.py
├── exceptions.py
├── conditions.py             ← new in v0.5.0
├── directory.py              ← new in v0.5.0
├── builder/
│   ├── __init__.py           ← re-exports all three builders
│   ├── raw_builder.py        ← RawConfigBuilder
│   ├── dataclass_builder.py  ← DataClassConfigBuilder (added in v0.3.0)
│   ├── config_builder.py     ← ConfigBuilder
│   └── _merge.py             ← _deep_merge (extracted in v0.3.0)
└── loaders/
    └── ...                   ← unchanged
```

## v1.0.0 — Advanced Features 📋 Target

Features that complete the differentiator story. Planned after v0.5.0 is stable.

**Secret Backend Loaders** — `from_secrets("aws://...")`, `from_secrets("vault://...")`. New `AWSSecretsLoader` and `VaultLoader` registered via `ConfigLoader.register_loader()`. Optional extras: `pip install pyconfigre[aws]`, `pyconfigre[vault]` and other secret backends.

**Config Watching (Hot Reload)** — `build(watch=True)` starts a daemon thread that polls mtime for registered file paths and swaps the config object atomically via `threading.Lock` on change.

## Labels and Milestones

Label definitions and branch conventions are maintained in `.github/config/`. See `.github/CONTRIBUTING.md` for the full reference.

Milestones map directly to the release sequence above. Each issue is assigned to the milestone it will ship in.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schema-less output | `build_dict()` on `RawConfigBuilder` | Exposes the pipeline before validation without undermining the typed identity of `ConfigBuilder` |
| Two-class split | `RawConfigBuilder` base + `ConfigBuilder` subclass | Clean inheritance, `_deep_merge` shared without coupling, honest `Generic[T]` |
| List merge behaviour | Replace, not extend | Lists in configs are complete values, not partial sequences to append |
| `_deep_merge` placement | Module-level in `builder.py` until folder conversion | Co-location is honest while only one consumer exists; extract to `_merge.py` at conversion |
| Folder conversion timing | At v0.3.0 (DataclassConfigBuilder) | Three builder classes justify the `builder/` package split |
| `from_env_layer` extension default | `.yaml` | Most common format; configurable via parameter |
| Integration test Python version | 3.10 only (minimum) | Packaging concern, not compatibility — unit tests cover all versions |
