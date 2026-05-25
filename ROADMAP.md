# PyConfigre — Development Roadmap

- Repository: https://github.com/aditya-barik/PyConfigre
- Package identity: A composable configuration assembly pipeline for Python. Load from any source, merge with intelligent priority, validate with Pydantic — or consume as a plain dict. Built for modern Python teams who want explicit, readable, testable configuration code.

## Release Timeline
```
    ●               ●               ◌               ◌               ◌
    │               │               │               │               │
────●───────────────●───────────────◌───────────────◌───────────────◌────
    │               │               │               │               │
  v0.1.0          v0.1.1          v0.2.0          v0.3.0          v1.0.0
  shipped         shipped         current         planned         target
  Feb 2026        Mar 2026
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

## v0.2.0 — RawConfigBuilder + build_dict() 🔄 Current

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
- Both classes in `builder.py` until v0.3.0 triggers folder conversion

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

## v0.3.0 — New Pipeline Features 📋 Planned

**Goal:** Ship the features that make PyConfigre meaningfully differentiated from `pydantic-settings` and `dynaconf`.

### Feature 3.1 — `from_env_layer()`

**Problem:** The base → {env} → local layering pattern is written manually in every real project. It should be a single method call.

```python
# Today — every project writes this manually
env = os.getenv("ENV", "development")
config = (
    ConfigBuilder(AppConfig)
    .from_file("config/base.yaml",   optional=True)
    .from_file(f"config/{env}.yaml", optional=True)
    .from_file("config/local.yaml",  optional=True)
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

### Implementation:

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
        self
        .from_file(directory / f"{base_name}{extension}",  optional=True)
        .from_file(directory / f"{env_value}{extension}",  optional=True)
        .from_file(directory / f"{local_name}{extension}", optional=True)
    )
```

**Tests to add:** 8 tests covering base file, env-specific file, missing files skipped, local override priority, env var respected, custom base name, custom extension, default env value.

### Feature 3.2 — Schema Inference (`infer_schema()`)

**Problem:** Writing a Pydantic model for a 50-key nested config file from scratch is the biggest adoption friction point for large existing projects.

**Solution:** Generate a Pydantic model skeleton from a loaded dict. Developers start with 90% of their schema and refine from there.

```python
raw = RawConfigBuilder().from_file("complex.yaml").build_dict()
schema_code = RawConfigBuilder.infer_schema(raw, name="AppConfig")
print(schema_code)  # → valid Python with nested BaseModel classes
```

### Type inference rules:

| Python value | Inferred type |
|--------------|---------------|
| `True` / `False` | `bool` |
| `42` | `int` |
| `3.14` | `float` |
| `"hello"` | `str` |
| `[1, 2, 3]` | `list[int]` (element type from first item) |
| `None` | `Any` |
| `{"host": "x"}` | new nested BaseModel subclass |

### Tests to add:
8 tests covering flat dict, nested subclass creation, bool-before-int ordering, None → Optional, list element inference, valid Python output (exec assertion), custom name, write-to-file.


### Feature 3.3 — Directory Loading (`from_directory()`)

**Problem:** Large projects organise configs as a folder of files. There is no way to load this structure into a single accessible namespace.

**Solution:** Load all supported files from a directory into a single namespace.

```python
cfg = load_directory("config/")
cfg.env.dev["host"]       # attribute access
cfg["env"]["dev"]["host"] # subscript access
```

**New module:** `pyconfigre/directory.py` — `ConfigNamespace` + `load_directory()`.

**Tests to add:** 14+ tests covering all access patterns, missing root, non-directory path, unknown extensions (silent skip and explicit raise), `to_dict()` round-trip, read-only enforcement, `recursive=False`, hidden file skipping, and pipeline integration.

**Feature 3.4 — Conditional Loading (`when=` parameter)**

**Problem:** Conditional source application today breaks the fluent chain with if blocks.

```python
# With conditions — stays fluent
config = (
    ConfigBuilder(AppConfig)
    .from_file("base.yaml")
    .from_file("dev.yaml",  when=env_is("ENV", "dev"))
    .from_file("prod.yaml", when=env_is("ENV", "prod"))
    .from_env("MYAPP_")
    .build()
)
```

**Condition forms:** callable, 2-tuple `("ENV", "dev")`, 3-tuple with operator (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`), `{"all": [...]}` / `{"any": [...]}` sets, and helpers `env_is()`, `env_in()`, `when_all()`, `when_any()`.

**New module:** `pyconfigre/conditions.py`.

**Tests to add:** 20+ tests covering all condition forms, all operators, `all`/`any` logic, error cases, helpers, and mixin integration.

**File structure at v0.3.0 (folder conversion)**

```
pyconfigre/
├── __init__.py
├── exceptions.py
├── conditions.py           ← new in v0.3.0
├── directory.py            ← new in v0.3.0
├── builder/                ← converted from builder.py
│   ├── __init__.py         ← re-exports ConfigBuilder, RawConfigBuilder
│   ├── config_builder.py   ← ConfigBuilder
│   ├── raw_builder.py      ← RawConfigBuilder
│   └── _merge.py           ← _deep_merge (extracted at folder conversion)
└── loaders/
    └── ...                 ← unchanged
```

## v1.0.0 — Advanced Features 📋 Target

Features that complete the differentiator story. Planned after v0.3.0 is stable.

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
| Folder conversion timing | At v0.3.0, not before | Two classes at v0.2.0 do not justify the `__init__.py` overhead |
| `from_env_layer` extension default | `.yaml` | Most common format; configurable via parameter |
| Integration test Python version | 3.10 only (minimum) | Packaging concern, not compatibility — unit tests cover all versions |
