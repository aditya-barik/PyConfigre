# 🚀 PyConfigre

**Configuration management for Python applications.** Elegant, type-safe, and built for real-world needs.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/github/aditya-barik/PyConfigre/graph/badge.svg?token=II8VJY2FOM)](https://codecov.io/github/aditya-barik/PyConfigre)
[![Type Safe](https://img.shields.io/badge/type%20safe-mypy-blue)](http://mypy-lang.org/)

PyConfigre bridges the gap between manual configuration management and heavyweight tools. It combines **Pydantic's robust validation** with support for **multiple formats** (YAML, JSON, TOML), **environment variables**, and a **fluent API** that reads like natural Python. Need the pipeline without a schema? PyConfigre has you covered with `RawConfigBuilder`. Whether you're building microservices, web applications, or CLI tools, PyConfigre handles configuration without getting in the way.

## ✨ Why PyConfigre?

**Configuration shouldn't be complicated.** Most tools either do too much or too little. PyConfigre fits the middle ground:

- **For teams** who want type safety without sacrificing simplicity
- **For projects** that need to merge configurations from multiple sources
- **For developers** who prefer explicit, readable code over magic configuration files

## 🎯 Core Features

- **📋 Multi-Format Loading**: YAML, JSON, TOML, environment variables, or Python dictionaries
- **✓ Type-Safe Validation**: Full Pydantic integration for bulletproof configuration
- **🔀 Smart Priority Handling**: Effortlessly merge multiple sources (file → env → dict)
- **⛓️ Fluent API**: Chainable methods that read naturally
- **🎯 Format Auto-Detection**: Automatically identify and parse files
- **🐍 Modern Python**: Full type hints and Python 3.10+ syntax
- **   Schema-Free Option**: Use `RawConfigBuilder` when you just need a merged `dict` — no Pydantic required
- **🪶 Lightweight**: Only `pydantic` and `pyyaml` required for core functionality

## 🚀 Getting Started

### Installation

```bash
# Basic installation (JSON & YAML support)
pip install pyconfigre

# Add TOML support
pip install pyconfigre[toml]

# With uv support
uv add pyconfigre
```

### 30-Second Example

```python
from pydantic import BaseModel
from pyconfigre import ConfigBuilder

class AppConfig(BaseModel):
    """Your application configuration schema."""
    debug: bool = False
    port: int = 8000
    host: str = "0.0.0.0"
    database_url: str

# Load from file → environment → runtime overrides
config = (
    ConfigBuilder(AppConfig)
    .from_file("config.yaml")
    .from_env("MYAPP_")
    .from_dict({"debug": True})
    .build()
)

# Type-safe access with IDE autocomplete
print(f"Server: {config.host}:{config.port}")
```

**That's it.** Three lines of configuration loading. Three sources merged intelligently. Full type safety throughout.

### Schema-Free Alternative

Don't need typed validation? Use `RawConfigBuilder` to get a plain dictionary:

```python
from pyconfigre import RawConfigBuilder

raw_config = (
    RawConfigBuilder()
    .from-file("config.yaml")
    .from_env("MYAPP_")
    .set("debug", True)  # Explicit override
    .build_dict()
)

# config is a plain dict — no schema needed
print(f"Port: {raw_config['port']}")
```

Same pipeline, same priority system, same multi-format support — just without the Pydantic model.

## � Common Patterns

### Pattern 1: File + Environment + Overrides

The most common real-world pattern:

```python
config = (
    ConfigBuilder(AppConfig)
    .from_file("config/default.yaml")      # Base configuration
    .from_env("MYAPP_")                    # Environment overrides
    .from_dict(runtime_overrides)          # Runtime values (highest priority)
    .build()
)
```

**Priority order** (lowest to highest): File → Environment → Dict → Explicit `.set()` method

### Pattern 2: Environment-Specific Configuration

Load different configurations per environment:

```python
import os

environment = os.getenv("ENV", "development")
config = (
    ConfigBuilder(AppConfig)
    .from_file(f"config/{environment}.yaml")        # Environment-specific base
    .from_file("config/local.yaml", optional=True)  # Local dev overrides
    .from_env("MYAPP_")
    .build()
)
```

### Pattern 3: Configuration with Nested Models

Structure complex configurations with nested Pydantic models:

```python
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    username: str
    password: str
    database: str

class CacheConfig(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 3600
    backend: str = "redis"

class AppConfig(BaseModel):
    app_name: str
    debug: bool = False
    database: DatabaseConfig
    cache: CacheConfig = Field(default_factory=CacheConfig)

config = ConfigBuilder(AppConfig).from_file("config.yaml").build()

# Access nested values with full type safety
print(f"DB: {config.database.host}:{config.database.port}")
print(f"Cache TTL: {config.cache.ttl_seconds}s")
```

### Pattern 4: Schema-Free Configuration

use `RawConfigBuilder` when you need the pipeline but not the validation — scripts, CLI tools, migrations, or quick prototypes:

```python
from pyconfigre import RawConfigBuilder

# Full pipeline, plain dict output
raw_config = (
    RawConfigBuilder()
    .from_file("config/default.yaml")
    .from_env("MYAPP_")
    .from_dict({"timeout": 30})
    .build_dict()
)

# inspect mid-chain without finalising
raw_builder = RawConfigBuilder().from_file("config.yaml")
print(raw_builder.peek())  # snapshot of current state
raw_builder.set("port", 9000)
raw_config = raw_builder.build_dict()
```

`RawConfigBuilder` shares the exact same loading, merging, and priority logic as `ConfigBuilder` — it just skips the Pydantic validation step.

### Pattern 5: Validation with Constraints

Let Pydantic enforce your business rules:

```python
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    port: int = Field(default=8000, ge=1, le=65535)      # Port range
    workers: int = Field(default=4, ge=1, le=256)        # Worker count
    timeout: float = Field(default=30.0, gt=0)           # Positive timeout
    environment: str = Field(default="production", pattern="^(dev|staging|production)$")

# Invalid config raises validation error
config = ConfigBuilder(AppConfig).from_dict({"port": 99999}).build()  # ❌ Fails validation
```

## 🎯 Configuration Priority

PyConfigre implements a simple, predictable priority system. Later sources override earlier ones:

```
File → Environment Variables → Dictionary → Explicit .set() method
↑                                            ↑
Lowest Priority                              Highest Priority
```

Example:
```python
# YAML file has: debug: false, port: 8000
# ENV var: MYAPP_DEBUG=true
# Dict: {"port": 3000}

config = (
    ConfigBuilder(AppConfig)
    .from_file("config.yaml")  # debug=false, port=8000
    .from_env("MYAPP_")        # debug=true (overrides file)
    .from_dict({"port": 3000}) # port=3000 (overrides both)
    .build()
)

# Result: debug=true, port=3000
```

This pattern matches how most systems expect configuration to work—sensible defaults in files, environment-specific overrides via env vars, and runtime tweaks via dictionaries.

## 📦 Supported Formats

| Format | File Extension | Dependency | Notes |
|--------|---|---|---|
| **YAML** | `.yaml`, `.yml` | `pyyaml` | Human-readable, widely used |
| **JSON** | `.json` | Built-in (stdlib) | Strict, universally supported |
| **TOML** | `.toml` | tomllib (3.11+) or tomli | Clean syntax, configuration standard |
| **Environment Variables** | — | Built-in | Perfect for secrets and overrides |
| **Python Dicts** | — | Built-in | Runtime configuration |

## 🏗️ Real-World Example: API Service

Here's a complete, production-like example:

```python
from pydantic import BaseModel, Field
from typing import Optional
from pyconfigre import ConfigBuilder

# Configuration schema
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    username: str
    password: str
    database: str

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "json"
    output: str = "stdout"

class AppConfig(BaseModel):
    app_name: str = "my-api"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    database: DatabaseConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    secret_key: Optional[str] = None

# Load configuration in your application startup
def setup_config() -> AppConfig:
    """Load and validate application configuration."""
    return (
        ConfigBuilder(AppConfig)
        .from_file("config/default.yaml")           # Defaults
        .from_file(f"config/{os.getenv('ENV')}.yaml", optional=True)
        .from_env("MYAPI_")                         # Override with env vars
        .build()
    )

# Usage
config = setup_config()
print(f"Starting {config.app_name} v{config.version}")
print(f"Listening on {config.host}:{config.port}")
print(f"Database: {config.database.host}")
```

**Configuration file** (`config/default.yaml`):
```yaml
app_name: my-api
version: 1.0.0
debug: false
database:
  host: localhost
  username: app_user
  password: ${DB_PASSWORD}  # Can use env vars or load separately
  database: app_db
logging:
  level: INFO
```

**Environment override** (`config/production.yaml`):
```yaml
debug: false
database:
  host: prod-db.example.com
  username: prod_user
logging:
  level: WARNING
```

This approach gives you:
- ✅ Type-safe configuration with validation
- ✅ Environment-specific configurations
- ✅ Secrets via environment variables
- ✅ Sensible defaults that developers can override locally
- ✅ Production ready

## 🧪 Testing Configuration

```python
import pytest
from pydantic import BaseModel, ValidationError
from pyconfigre import ConfigBuilder

class TestConfig(BaseModel):
    feature_enabled: bool = False
    api_key: str

def test_config_validation():
    """Test that invalid config raises ValidationError."""
    with pytest.raises(ValidationError):
        ConfigBuilder(TestConfig).from_dict({}).build()  # Missing required api_key

def test_config_building():
    """Test successful configuration building."""
    config = (
        ConfigBuilder(TestConfig)
        .from_dict({"api_key": "test-key"})
        .set("feature_enabled", True)
        .build()
    )
    assert config.feature_enabled is True
    assert config.api_key == "test-key"

def test_config_priority():
    """Test configuration priority (file < env < dict)."""
    config = (
        ConfigBuilder(TestConfig)
        .from_dict({"api_key": "from-dict", "feature_enabled": False})
        .from_dict({"api_key": "from-second-dict"})  # Overrides
        .build()
    )
    assert config.api_key == "from-second-dict"  # Later dict wins
```

## ✅ Best Practices

1. **Define configuration schemas early** – Use Pydantic models as your configuration contract
2. **Use environment variables for secrets** – Never hardcode API keys, passwords, or tokens
3. **Provide sensible defaults** – Make common values optional so developers have fewer things to configure
4. **Fail fast on invalid config** – Call `.build()` early in your app startup, not lazily
5. **Test your configuration** – Write tests that verify config loading from different sources
6. **Version your schema** – Document breaking changes to your config structure
7. **Use type hints everywhere** – Let IDE autocomplete guide developers using your app

## 🔐 Security Considerations

**Never hardcode secrets:**
```python
# ❌ DON'T DO THIS
config = ConfigBuilder(AppConfig).from_dict({
    "api_key": "sk-1234567890abcdef"
}).build()

# ✅ DO THIS
config = (
    ConfigBuilder(AppConfig)
    .from_file("config.yaml")  # No secrets in file
    .from_env("MYAPP_")        # Get secrets from environment
    .build()
)
```

**Use strong validation:**
```python
from pydantic import BaseModel, Field

class SecureConfig(BaseModel):
    api_key: str = Field(min_length=32)                        # Enforce minimum length
    timeout: float = Field(gt=0)                               # Must be positive
    environment: str = Field(pattern="^(dev|staging|prod)$")   # Whitelist values

# Invalid config is rejected before it can cause problems
config = ConfigBuilder(SecureConfig).from_env("APP_").build()  # Fails fast if invalid
```

**Restrict file permissions:**
```bash
# Ensure config files with sensitive data are readable only by your app
chmod 600 config/production.yaml
```

## 📊 Project Status

| Aspect | Status |
|--------|--------|
| **Version** | 0.2.0 |
| **Python Support** | 3.10, 3.11, 3.12, 3.13, 3.14 |
| **Test Coverage** | ~100% (200 tests) |
| **Type Checking** | Full MyPy strict compliance |
| **CI/CD** | GitHub Actions (multi-version testing) |

## 🤝 Contributing

Contributions are welcome! Whether it's:
- Bug reports or feature requests (open an issue)
- Documentation improvements
- Code contributions (fork and submit a PR)

Please follow the existing code style and include tests for new features.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

### 👤 Aditya Barik

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/aditya-barik)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/aditya-barik/)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:aditya.barik@outlook.com)

---

**Questions or feedback?** Open an issue on [GitHub](https://github.com/aditya-barik/PyConfigre/issues).

Built with ❤️ for teams who care about clean, maintainable, type-safe Python code.
