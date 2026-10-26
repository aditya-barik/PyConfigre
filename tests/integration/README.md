# Integration Test Suite

> **137 tests** · **14 files** · every realistic use case PyConfigre supports.

This guide walks through the integration suite scenario by scenario. Each section maps to a single test file and explains *what real-world problem* the tests simulate, not just what code they call.

---

## Table of Contents

| # | Section | File | Tests |
|--:|---------|------|:-----:|
| 1 | [Loading YAML Files](#1-loading-yaml-files) | [`test_yaml_loading.py`](./test_yaml_loading.py) | 7 |
| 2 | [Loading JSON Files](#2-loading-json-files) | [`test_json_loading.py`](./test_json_loading.py) | 5 |
| 3 | [Loading TOML Files](#3-loading-toml-files) | [`test_toml_loading.py`](./test_toml_loading.py) | 4 |
| 4 | [Environment Variables](#4-loading-from-environment-variables) | [`test_env_loading.py`](./test_env_loading.py) | 11 |
| 5 | [Multi-Source Merging](#5-multi-source-merging) | [`test_multi_source_merging.py`](./test_multi_source_merging.py) | 8 |
| 6 | [Optional Files](#6-optional-file-loading) | [`test_optional_files.py`](./test_optional_files.py) | 5 |
| 7 | [Unsupported Formats](#7-unsupported-file-formats) | [`test_unsupported_formats.py`](./test_unsupported_formats.py) | 5 |
| 8 | [Fluent API](#8-fluent-api-ergonomics) | [`test_fluent_api.py`](./test_fluent_api.py) | 6 |
| 9 | [Schema Validation](#9-schema-validation) | [`test_validation.py`](./test_validation.py) | 25 |
| 10 | [RawConfigBuilder](#10-rawconfigbuilder-schema-less) | [`test_raw_builder.py`](./test_raw_builder.py) | 16 |
| 11 | [Conditional Loading](#11-conditional-loading) | [`test_conditional_loading.py`](./test_conditional_loading.py) | 13 |
| 12 | [Environment Layers](#12-environment-layered-loading) | [`test_env_layer_loading.py`](./test_env_layer_loading.py) | 9 |
| 13 | [Directory Loading](#13-directory-loading) | [`test_directory_loading.py`](./test_directory_loading.py) | 15 |
| 14 | [Schema Inference](#14-schema-inference) | [`test_schema_inference.py`](./test_schema_inference.py) | 8 |
| | | **Total** | **137** |

---

## How to Read This Guide

- **Sections 1–3** test file-format parsing. They use `ConfigBuilder` because `from_file()` lives on `RawConfigBuilder` (the base class) and is inherited identically by all three builders — the parsing path is shared code. Builder-specific validation is covered in [Section 9](#9-schema-validation). File loading through `RawConfigBuilder` is exercised in [Section 10](#10-rawconfigbuilder-schema-less), and through `DataClassConfigBuilder` in [Section 5](#5-multi-source-merging) and [Section 12](#12-environment-layered-loading).
- **Sections 4–8** test core pipeline mechanics: env vars, merging, optional files, unsupported formats, and fluent API ergonomics.
- **Sections 9–10** test validation and schema-less usage.
- **Sections 11–14** test v0.4.0 features: conditional loading, env layers, directory loading, and schema inference.

---

## 1. Loading YAML Files

**Scenario:** Loading `.yaml` and `.yml` configuration files through
the shared `from_file()` pipeline, verified via `ConfigBuilder` with Pydantic
models.  Edge cases include empty files and parse errors.

**File:** [`tests/integration/test_yaml_loading.py`](./test_yaml_loading.py) · **7 tests**

### [`TestYAMLLoading`](./test_yaml_loading.py#L17)

| Test | Scenario |
|------|----------|
| [`test_flat_yaml`](./test_yaml_loading.py#L20) | Load a simple flat YAML file and verify all keys reach the Pydantic model. |
| [`test_nested_yaml`](./test_yaml_loading.py#L32) | Load YAML with nested mappings (server, database sections) — verifies nested Pydantic model construction. |
| [`test_all_primitive_types`](./test_yaml_loading.py#L77) | A YAML file with `str`, `int`, `float`, `bool` — verifies type preservation through the pipeline. |
| [`test_empty_yaml_uses_defaults`](./test_yaml_loading.py#L109) | An empty YAML file produces a valid config using Pydantic field defaults. |
| [`test_yml_extension`](./test_yaml_loading.py#L121) | The `.yml` extension is treated identically to `.yaml`. |
| [`test_yaml_list_root_raises`](./test_yaml_loading.py#L131) | A YAML file whose root is a list (not a mapping) raises `ConfigLoadError`. |
| [`test_yaml_parse_error`](./test_yaml_loading.py#L144) | Malformed YAML raises `ConfigLoadError` with the parser's message. |

---

## 2. Loading JSON Files

**Scenario:** Loading `.json` configuration files through the shared
`from_file()` pipeline, including type fidelity and error handling.

**File:** [`tests/integration/test_json_loading.py`](./test_json_loading.py) · **5 tests**

### [`TestJSONLoading`](./test_json_loading.py#L17)

| Test | Scenario |
|------|----------|
| [`test_flat_json`](./test_json_loading.py#L20) | Load a flat JSON object into a Pydantic model. |
| [`test_nested_json`](./test_json_loading.py#L39) | Load nested JSON with server/database/cache objects — verifies nested model construction. |
| [`test_all_primitive_types`](./test_json_loading.py#L72) | JSON with `str`, `int`, `float`, `bool`, `null` — type preservation. |
| [`test_malformed_json`](./test_json_loading.py#L99) | Invalid JSON syntax raises `ConfigLoadError`. |
| [`test_json_array_root_raises`](./test_json_loading.py#L107) | A JSON file whose root is an array raises `ConfigValidationError`. |

---

## 3. Loading TOML Files

**Scenario:** Loading `.toml` configuration files through the shared
`from_file()` pipeline, with tables and primitive types.

**File:** [`tests/integration/test_toml_loading.py`](./test_toml_loading.py) · **4 tests**

### [`TestTOMLLoading`](./test_toml_loading.py#L18)

| Test | Scenario |
|------|----------|
| [`test_flat_toml`](./test_toml_loading.py#L21) | Load a flat TOML file into a Pydantic model. |
| [`test_nested_toml_tables`](./test_toml_loading.py#L38) | TOML tables (`[server]`, `[database]`) map to nested Pydantic models. |
| [`test_all_primitive_types`](./test_toml_loading.py#L76) | TOML with `str`, `int`, `float`, `bool` — type preservation. |
| [`test_toml_parse_error`](./test_toml_loading.py#L102) | Invalid TOML syntax raises `ConfigLoadError`. |

---

## 4. Loading from Environment Variables

**Scenario:** Real-world environment variable loading — prefixed
variables, nested keys via `__`, type parsing, and dataclass coercion.

**File:** [`tests/integration/test_env_loading.py`](./test_env_loading.py) · **11 tests**

### [`TestENVLoading`](./test_env_loading.py#L17) — Pydantic builder (8 tests)

| Test | Scenario |
|------|----------|
| [`test_flat_env_vars_with_prefix`](./test_env_loading.py#L20) | Prefixed env vars (`SVC_`) are stripped and mapped to Pydantic model fields. |
| [`test_double_underscore_nesting`](./test_env_loading.py#L35) | `MYAPP__SERVER__HOST` expands into nested config structures (v0.1.1 fix). |
| [`test_no_prefix_loads_all_vars`](./test_env_loading.py#L63) | Without a prefix, all environment variables are loaded. |
| [`test_strip_prefix_false_keeps_prefix_in_key`](./test_env_loading.py#L78) | `strip_prefix=False` retains the prefix as part of the key name. |
| [`test_lowercase_false_preserves_original_case`](./test_env_loading.py#L87) | `lowercase=False` keeps the original uppercase env var names. |
| [`test_nested_false_keeps_double_underscore_flat`](./test_env_loading.py#L96) | `nested=False` prevents `__` from being treated as a separator. |
| [`test_all_value_types_parsed`](./test_env_loading.py#L106) | String env values are coerced to `int`, `float`, `bool` automatically. |
| [`test_integer_parses_as_int_not_float`](./test_env_loading.py#L128) | `"8000"` → `8000` (int), not `8000.0` (float). Parse-order fix from v0.1.1. |

### [`TestDataClassENVCoercion`](./test_env_loading.py#L146) — Dataclass builder (3 tests)

| Test | Scenario |
|------|----------|
| [`test_env_strings_coerced_to_field_types`](./test_env_loading.py#L149) | String env vars are coerced to dataclass field types (`int`, `float`, `bool`). |
| [`test_falsy_bool_strings_from_env`](./test_env_loading.py#L166) | Falsy strings (`"no"`, `"false"`, `"0"`) coerce to `False` for `bool` fields. |
| [`test_nested_env_vars_instantiate_dataclasses`](./test_env_loading.py#L177) | Double-underscore env vars produce nested dataclass instances. |

---

## 5. Multi-Source Merging

**Scenario:** The core value proposition — assembling configuration
from multiple sources with deterministic priority.

**File:** [`tests/integration/test_multi_source_merging.py`](./test_multi_source_merging.py) · **8 tests**

### [`TestMultiSourceMerging`](./test_multi_source_merging.py#L18)

| Test | Scenario |
|------|----------|
| [`test_file_env_dict_priority_chain`](./test_multi_source_merging.py#L21) | file < env < dict: each layer overrides only what it touches. |
| [`test_two_files_second_wins_on_conflict`](./test_multi_source_merging.py#L43) | When two files share a key, the second file's value wins. |
| [`test_dict_wins_over_file`](./test_multi_source_merging.py#L57) | `from_dict()` applied after `from_file()` overrides conflicting keys. |
| [`test_deep_nested_partial_override`](./test_multi_source_merging.py#L73) | A partial override merges into nested dicts without clobbering sibling keys. |
| [`test_list_in_later_source_replaces_entirely`](./test_multi_source_merging.py#L103) | Lists are replaced wholesale — no append/extend. |
| [`test_set_is_highest_priority`](./test_multi_source_merging.py#L128) | `set()` applied last wins over every other source. |
| [`test_peek_shows_intermediate_state`](./test_multi_source_merging.py#L144) | `peek()` snapshots the merged state mid-pipeline without consuming the builder. |
| [`test_dataclass_multi_source_priority`](./test_multi_source_merging.py#L165) | The same file < env < dict priority chain works through `DataClassConfigBuilder`. |

---

## 6. Optional File Loading

**Scenario:** Graceful handling of missing files — fallback
patterns, optional overrides, and required-file enforcement.

**File:** [`tests/integration/test_optional_files.py`](./test_optional_files.py) · **5 tests**

### [`TestOptionalFiles`](./test_optional_files.py#L18)

| Test | Scenario |
|------|----------|
| [`test_optional_missing_file_is_silently_skipped`](./test_optional_files.py#L21) | `optional=True` with a missing file produces no error — defaults are used. |
| [`test_optional_existing_file_loads_normally`](./test_optional_files.py#L34) | `optional=True` with an existing file loads it normally. |
| [`test_optional_missing_file_env_provides_all_values`](./test_optional_files.py#L44) | Missing optional file + env vars = complete config (CI/CD pattern). |
| [`test_required_missing_file_raises`](./test_optional_files.py#L68) | `optional=False` (default) with a missing file raises `ConfigNotFoundError`. |
| [`test_base_required_environment_override_optional`](./test_optional_files.py#L75) | Required base file + optional env-specific override — the canonical deployment pattern. |

---

## 7. Unsupported File Formats

**Scenario:** Clear error messages for unsupported extensions and
the custom loader registration escape hatch.

**File:** [`tests/integration/test_unsupported_formats.py`](./test_unsupported_formats.py) · **5 tests**

### [`TestUnsupportedFormats`](./test_unsupported_formats.py#L18)

| Test | Scenario |
|------|----------|
| [`test_ini_file_exists_raises_value_error`](./test_unsupported_formats.py#L21) | A `.ini` file raises `ValueError` — not `FileNotFoundError`. |
| [`test_cfg_file_exists_raises_value_error`](./test_unsupported_formats.py#L33) | A `.cfg` file raises `ValueError` — same behavior. |
| [`test_unsupported_extension_missing_file_raises_value_error`](./test_unsupported_formats.py#L41) | Extension is validated *before* checking file existence (Issue-1 fix). |
| [`test_optional_true_does_not_suppress_bad_extension`](./test_unsupported_formats.py#L54) | `optional=True` does not suppress unsupported-extension errors. |
| [`test_custom_loader_makes_extension_supported`](./test_unsupported_formats.py#L67) | `ConfigLoader.register_loader()` makes a custom extension work end-to-end. |

---

## 8. Fluent API Ergonomics

**Scenario:** Builder chaining, `peek()` non-destructive snapshots,
dot-notation `set()`, and clear error messages.

**File:** [`tests/integration/test_fluent_api.py`](./test_fluent_api.py) · **6 tests**

### [`TestFluentAPI`](./test_fluent_api.py#L18)

| Test | Scenario |
|------|----------|
| [`test_all_source_methods_chain`](./test_fluent_api.py#L21) | Chain `from_file` → `from_env` → `from_dict` → `set` → `build` in a single expression. |
| [`test_peek_does_not_affect_build`](./test_fluent_api.py#L41) | `peek()` mid-chain does not consume or alter builder state. |
| [`test_peek_returns_independent_copy`](./test_fluent_api.py#L62) | Mutating the `peek()` dict does not affect the builder's internal state. |
| [`test_set_creates_nested_path_with_dot_notation`](./test_fluent_api.py#L79) | `set("server.host", "0.0.0.0")` creates nested dict structure. |
| [`test_set_raises_clear_error_on_scalar_intermediate`](./test_fluent_api.py#L95) | Setting a nested key under a scalar (`"name.sub"` where `name` is a string) raises a clear `TypeError`. |
| [`test_builder_is_reusable_after_peek`](./test_fluent_api.py#L115) | `peek()` is non-terminal — sources can be added after peeking, `build()` includes everything. |

---

## 9. Schema Validation

**Scenario:** Type enforcement and field validation through both
`ConfigBuilder` (Pydantic) and `DataClassConfigBuilder` (dataclasses),
including `unknown_fields` and `missing_fields` modes.

**File:** [`tests/integration/test_validation.py`](./test_validation.py) · **25 tests**

### [`TestValidation`](./test_validation.py#L31) — Pydantic validation (7 tests)

| Test | Scenario |
|------|----------|
| [`test_valid_config_returns_typed_model`](./test_validation.py#L34) | A correct YAML file produces a typed Pydantic model instance. |
| [`test_missing_required_field_raises`](./test_validation.py#L46) | Omitting a required Pydantic field raises `ConfigValidationError`. |
| [`test_wrong_type_raises`](./test_validation.py#L61) | A string where an int is expected raises `ConfigValidationError`. |
| [`test_field_constraint_violated_raises`](./test_validation.py#L73) | A port outside `ge=1, le=65535` raises `ConfigValidationError`. |
| [`test_nested_model_validated_correctly`](./test_validation.py#L97) | Nested Pydantic models are recursively validated. |
| [`test_optional_field_accepts_none`](./test_validation.py#L116) | `Optional` fields accept `None` without error. |
| [`test_invalid_type_caught_at_build_not_at_set`](./test_validation.py#L131) | `set()` accepts any type — validation fires only at `build()`. |

### [`TestDataClassValidation`](./test_validation.py#L151) — Dataclass validation (15 tests)

| Test | Scenario |
|------|----------|
| [`test_empty_config_uses_defaults`](./test_validation.py#L154) | No sources → all dataclass defaults are used. |
| [`test_string_values_coerced_from_dict`](./test_validation.py#L163) | String values are coerced to `int`, `float`, `bool` for dataclass fields. |
| [`test_invalid_bool_string_raises`](./test_validation.py#L192) | An unrecognised bool string (e.g. `"maybe"`) raises `ConfigValidationError`. |
| [`test_bool_value_for_int_field_is_coerced_to_int`](./test_validation.py#L201) | A `bool` value for an `int` field is coerced to `0`/`1`. |
| [`test_falsy_bool_string_from_dict`](./test_validation.py#L211) | `"no"`, `"false"`, `"0"`, `"off"` coerce to `False`. |
| [`test_unrecognised_type_string_passes_through`](./test_validation.py#L221) | A string value for a non-coercible type (e.g. `complex`) passes through unchanged. |
| [`test_missing_required_field_raises`](./test_validation.py#L229) | A required dataclass field (no default) raises `ConfigValidationError`. |
| [`test_non_dataclass_schema_raises`](./test_validation.py#L244) | Passing a plain class (not a `@dataclass`) raises `TypeError`. |
| [`test_invalid_unknown_fields_value_raises`](./test_validation.py#L253) | An invalid `unknown_fields` mode (e.g. `"invalid"`) raises `ValueError`. |
| [`test_unknown_fields_warn_by_default`](./test_validation.py#L258) | Extra keys emit a `UserWarning` by default. |
| [`test_unknown_fields_ignore_mode`](./test_validation.py#L277) | `unknown_fields="ignore"` silently drops extra keys. |
| [`test_unknown_fields_forbid_mode`](./test_validation.py#L292) | `unknown_fields="forbid"` raises `ConfigValidationError` on extra keys. |
| [`test_missing_fields_forbid_by_default`](./test_validation.py#L305) | Default `missing_fields="forbid"` raises on missing required fields. |
| [`test_missing_fields_warn`](./test_validation.py#L314) | `missing_fields="warn"` warns, then schema validation still fails. |
| [`test_missing_fields_ignore`](./test_validation.py#L326) | `missing_fields="ignore"` skips the pre-check, schema validation still fails. |

### [`TestConfigBuilderMissingFields`](./test_validation.py#L339) — Pydantic missing_fields (3 tests)

| Test | Scenario |
|------|----------|
| [`test_missing_fields_forbid_by_default`](./test_validation.py#L342) | Default `missing_fields="forbid"` raises on missing Pydantic required fields. |
| [`test_missing_fields_warn`](./test_validation.py#L351) | `missing_fields="warn"` warns, then Pydantic validation still fails. |
| [`test_missing_fields_ignore`](./test_validation.py#L361) | `missing_fields="ignore"` skips pre-check, Pydantic validation still fails. |

---

## 10. RawConfigBuilder (Schema-Less)

**Scenario:** `RawConfigBuilder` as a standalone tool — no Pydantic,
no dataclasses, just dict-in / dict-out.  Covers the same merging and
priority semantics as typed builders, plus `unknown_fields` and
`missing_fields` validation with manual key sets.

**File:** [`tests/integration/test_raw_builder.py`](./test_raw_builder.py) · **16 tests**

### [`TestRawBuilderMultiSource`](./test_raw_builder.py#L21) — Multi-source merging (9 tests)

| Test | Scenario |
|------|----------|
| [`test_file_env_dict_set_priority`](./test_raw_builder.py#L24) | Full priority chain (file < env < dict < set) as a plain dict. |
| [`test_deep_merge_preserves_siblings`](./test_raw_builder.py#L43) | A partial YAML override merges without clobbering sibling nested keys. |
| [`test_list_replaced_not_appended`](./test_raw_builder.py#L67) | Lists are replaced wholesale, not merged. |
| [`test_two_files_different_formats`](./test_raw_builder.py#L84) | YAML base + JSON override merge correctly across formats. |
| [`test_peek_returns_independent_snapshot`](./test_raw_builder.py#L103) | `peek()` returns a deep copy — mutations do not affect the builder. |
| [`test_peek_then_continue_building`](./test_raw_builder.py#L118) | `peek()` is non-terminal — sources can be added after peeking. |
| [`test_empty_builder_returns_empty_dict`](./test_raw_builder.py#L133) | A builder with no sources returns `{}`. |
| [`test_build_dict_returns_independent_copy`](./test_raw_builder.py#L138) | `build_dict()` returns a deep copy — repeated calls are independent. |
| [`test_set_dot_notation_creates_nested_path`](./test_raw_builder.py#L148) | Dot-separated keys (`"database.host"`) create nested dict structures. |

### [`TestRawBuilderFieldValidation`](./test_raw_builder.py#L164) — Field validation (7 tests)

| Test | Scenario |
|------|----------|
| [`test_unknown_fields_warn_by_default`](./test_raw_builder.py#L167) | Extra keys beyond `expected_keys` emit a `UserWarning`. |
| [`test_unknown_fields_forbid`](./test_raw_builder.py#L176) | `unknown_fields="forbid"` raises `ConfigValidationError` on extra keys. |
| [`test_unknown_fields_ignore`](./test_raw_builder.py#L186) | `unknown_fields="ignore"` silently allows extra keys. |
| [`test_missing_fields_forbid_by_default`](./test_raw_builder.py#L201) | Missing keys from `required_keys` raise `ConfigValidationError`. |
| [`test_missing_fields_warn`](./test_raw_builder.py#L210) | `missing_fields="warn"` emits a warning instead of raising. |
| [`test_missing_fields_ignore`](./test_raw_builder.py#L224) | `missing_fields="ignore"` silently allows missing keys. |
| [`test_combined_unknown_and_missing_validation`](./test_raw_builder.py#L239) | Both unknown and missing field checks fire in one `build_dict()` call. |

---

## 11. Conditional Loading

**Scenario:** The `when=` parameter on builder source methods.
Real applications load different configuration depending on deployment
environment — these tests simulate that with `env_is()`, `env_in()`,
`when_all()`, and `when_any()`.

**File:** [`tests/integration/test_conditional_loading.py`](./test_conditional_loading.py) · **13 tests**

### [`TestConditionalLoading`](./test_conditional_loading.py#L25)

| Test | Scenario |
|------|----------|
| [`test_dev_only_file_loaded_in_dev`](./test_conditional_loading.py#L28) | A dev config file is loaded when `APP_ENV=dev`. |
| [`test_dev_only_file_skipped_in_prod`](./test_conditional_loading.py#L48) | The same dev file is skipped when `APP_ENV=prod`. |
| [`test_env_in_loads_for_matching_environments`](./test_conditional_loading.py#L67) | `env_in("DEPLOY_ENV", ["staging", "prod"])` loads secrets for matching envs. |
| [`test_env_in_skips_for_excluded_environment`](./test_conditional_loading.py#L85) | `env_in()` skips the source when the env var is not in the set. |
| [`test_when_all_requires_both_conditions`](./test_conditional_loading.py#L103) | `when_all(env_is(...), env_is(...))` loads only when both conditions are true. |
| [`test_when_all_skips_when_one_condition_fails`](./test_conditional_loading.py#L127) | `when_all()` skips when any sub-condition is false. |
| [`test_when_any_loads_if_one_matches`](./test_conditional_loading.py#L151) | `when_any(env_is("staging"), env_is("prod"))` loads when at least one matches. |
| [`test_conditional_env_loading`](./test_conditional_loading.py#L175) | `from_env("PROD_", when=env_is("APP_ENV", "prod"))` — conditional env var loading. |
| [`test_conditional_env_skipped`](./test_conditional_loading.py#L188) | The same conditional env source is skipped when the condition is false. |
| [`test_conditional_dict_override`](./test_conditional_loading.py#L201) | `from_dict({...}, when=env_is("FEATURE_FLAG", "enabled"))` — feature-flag-driven overrides. |
| [`test_conditional_set`](./test_conditional_loading.py#L216) | `set("port", 9999, when=env_is("OVERRIDE_PORT", "yes"))` — conditional single-value override. |
| [`test_multi_conditional_pipeline`](./test_conditional_loading.py#L228) | Full pipeline: base file + conditional env file + conditional env vars + conditional set — all in one chain. |
| [`test_raw_builder_conditional_loading`](./test_conditional_loading.py#L258) | `when=` works on `RawConfigBuilder` (schema-less) pipelines too. |

---

## 12. Environment-Layered Loading

**Scenario:** The `from_env_layer()` convenience method — the
`base.yaml → {env}.yaml → local.yaml` pattern that most web frameworks use.
Tested across all three builders.

**File:** [`tests/integration/test_env_layer_loading.py`](./test_env_layer_loading.py) · **9 tests**

### [`TestEnvLayerLoading`](./test_env_layer_loading.py#L20)

| Test | Scenario |
|------|----------|
| [`test_full_layer_stack`](./test_env_layer_loading.py#L23) | `base.yaml` → `production.yaml` → `local.yaml` — all three layers merge with correct priority. |
| [`test_dev_environment_default`](./test_env_layer_loading.py#L42) | When the env var is unset, the layer defaults to `development.yaml`. |
| [`test_missing_layers_silently_skipped`](./test_env_layer_loading.py#L57) | Only `base.yaml` exists — missing env/local files are silently skipped. |
| [`test_env_layer_then_env_vars_override`](./test_env_layer_loading.py#L70) | **Canonical pattern:** file layers provide structure, env vars inject secrets on top. |
| [`test_env_layer_with_json_extension`](./test_env_layer_loading.py#L96) | `extension=".json"` switches from YAML to JSON files. |
| [`test_env_layer_custom_names`](./test_env_layer_loading.py#L113) | `base_name="defaults"` and `local_name="overrides"` customise file names. |
| [`test_env_layer_with_dataclass_builder`](./test_env_layer_loading.py#L129) | `from_env_layer()` works through `DataClassConfigBuilder`. |
| [`test_env_layer_with_raw_builder`](./test_env_layer_loading.py#L146) | `from_env_layer()` works through `RawConfigBuilder` (schema-less). |
| [`test_env_layer_combined_with_directory`](./test_env_layer_loading.py#L161) | **Composite pattern:** env layers for app-level config + `from_directory()` for component configs. |

---

## 13. Directory Loading

**Scenario:** Loading all config files from a directory into a
`ConfigNamespace`, and the builder's `from_directory()` pipeline method.
Covers mixed formats, hidden files, error handling, and deployment
patterns.

**File:** [`tests/integration/test_directory_loading.py`](./test_directory_loading.py) · **15 tests**

### [`TestLoadDirectory`](./test_directory_loading.py#L21) — Standalone `load_directory()` (10 tests)

| Test | Scenario |
|------|----------|
| [`test_load_multiple_yaml_files`](./test_directory_loading.py#L24) | Each YAML file becomes a namespace key (`server.yaml` → `ns.server`). |
| [`test_mixed_formats_in_directory`](./test_directory_loading.py#L37) | YAML, JSON, and TOML files coexist in one directory. |
| [`test_namespace_attribute_and_dict_access`](./test_directory_loading.py#L51) | `ConfigNamespace` supports both `ns.app["name"]` and `ns["app"]["name"]`. |
| [`test_namespace_contains_check`](./test_directory_loading.py#L60) | The `in` operator works on namespace keys. |
| [`test_namespace_is_read_only`](./test_directory_loading.py#L69) | Attribute assignment raises `AttributeError` — namespaces are immutable. |
| [`test_hidden_files_skipped_by_default`](./test_directory_loading.py#L78) | Files starting with `.` are silently skipped. |
| [`test_unsupported_extensions_skipped_by_default`](./test_directory_loading.py#L89) | `.txt`, `.md`, and other non-config files are silently skipped. |
| [`test_unsupported_extensions_raise_mode`](./test_directory_loading.py#L101) | `unknown_extensions="raise"` raises `ValueError` on unsupported files. |
| [`test_nonexistent_directory_raises`](./test_directory_loading.py#L109) | A nonexistent path raises `ConfigNotFoundError`. |
| [`test_file_path_raises`](./test_directory_loading.py#L114) | Passing a file path (not a directory) raises `ConfigLoadError`. |

### [`TestFromDirectory`](./test_directory_loading.py#L124) — Builder pipeline (5 tests)

| Test | Scenario |
|------|----------|
| [`test_directory_merged_into_pipeline`](./test_directory_loading.py#L127) | `from_directory()` merges all directory files into the builder state. |
| [`test_directory_then_env_override`](./test_directory_loading.py#L146) | **Deployment pattern:** directory defaults + env var overrides for production. |
| [`test_directory_combined_with_file`](./test_directory_loading.py#L180) | Single base file + directory of component configs merged into one pipeline. |
| [`test_from_directory_with_when_false`](./test_directory_loading.py#L206) | `from_directory(..., when=lambda: False)` skips the entire directory. |
| [`test_empty_directory_produces_empty_namespace`](./test_directory_loading.py#L221) | An empty directory contributes nothing to the pipeline. |

---

## 14. Schema Inference

**Scenario:** Generating Pydantic `BaseModel` source code from raw
configuration data — the prototyping workflow where you load a config
and auto-generate a starting-point schema.

**File:** [`tests/integration/test_schema_inference.py`](./test_schema_inference.py) · **8 tests**

### [`TestSchemaInference`](./test_schema_inference.py#L15)

| Test | Scenario |
|------|----------|
| [`test_infer_from_flat_yaml`](./test_schema_inference.py#L18) | Load a flat YAML file → `infer_schema()` → output contains correct field types. |
| [`test_infer_from_nested_config`](./test_schema_inference.py#L31) | Nested YAML → nested `BaseModel` subclasses (`ServerConfig`, `DatabaseConfig`). |
| [`test_infer_from_json_config`](./test_schema_inference.py#L54) | JSON with `str`, `int`, `float`, `bool`, `list[str]` → correct type annotations. |
| [`test_infer_writes_to_file`](./test_schema_inference.py#L77) | `output_file=` parameter writes the generated source to disk. |
| [`test_generated_source_is_valid_python`](./test_schema_inference.py#L89) | The generated source compiles without syntax errors (`compile()`). |
| [`test_infer_from_multi_source_pipeline`](./test_schema_inference.py#L104) | Schema inference on data assembled from YAML + JSON pipeline. |
| [`test_infer_from_directory_loaded_config`](./test_schema_inference.py#L125) | Schema inference from `from_directory()` — directory → schema in one flow. |
| [`test_infer_empty_dict`](./test_schema_inference.py#L139) | An empty config dict produces a model with `pass`. |

---

## Running the Integration Tests

```bash
# All integration tests
uv run pytest tests/integration/ -v

# A single file
uv run pytest tests/integration/test_conditional_loading.py -v

# A single test
uv run pytest tests/integration/test_validation.py::TestDataClassValidation::test_unknown_fields_warn_by_default -v

# Collect without running (verify count)
uv run pytest tests/integration/ --co -q | tail -1
```
