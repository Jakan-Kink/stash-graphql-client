# stash-graphql-client

[![PyPI version](https://badge.fury.io/py/stash-graphql-client.svg)](https://badge.fury.io/py/stash-graphql-client)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![codecov](https://codecov.io/gh/Jakan-Kink/stash-graphql-client/branch/main/graph/badge.svg?token=qtamVrMS5r)](https://codecov.io/gh/Jakan-Kink/stash-graphql-client)

Async Python client for [Stash](https://stashapp.cc) GraphQL API.

## 🔗 Quick Links

- 📦 **[PyPI Package](https://pypi.org/project/stash-graphql-client/)** - Install via pip
- 📚 **[Documentation](https://jakan-kink.github.io/stash-graphql-client/)** - Full API reference and guides
- 🎬 **[Stash Project](https://github.com/stashapp/stash)** - Upstream media server this client connects to
- 📝 **[Changelog](CHANGELOG.md)** - Version history and release notes
- 🤝 **[Contributing](CONTRIBUTING.md)** - Development guide and contribution guidelines
- 🔒 **[Security Policy](SECURITY.md)** - Vulnerability reporting and security best practices

## Features

- **ORM-like interface for GraphQL**: Use `.save()`, `.delete()`, and relationship helpers instead of writing mutations manually.
- **Identity map with Pydantic v2 wrap validators**: Same entity ID = same Python object reference. Nested objects with IDs are automatically separated into the identity map. Caching integrated at model construction—no separate cache layer needed.
- **Smart partial updates**: UNSET sentinel marks fields have not been requested or received data from the server. Fields you change get sent in mutations. UNSET is also part of the three-state logic for knowing the difference between unknown and intentionally NULL.
- **Type-safe with Pydantic v2**: Full runtime validation, IDE autocomplete, and error detection at development time.
- **Django-style filtering**: Familiar `rating100__gte=80` syntax instead of building complex GraphQL filter objects.
- **Lazy field population**: `populate()` fetches only missing fields with nested `__` syntax (`files__path`, `studio__parent__name`). `filter_and_populate()` and `populated_filter_iter()` combine filtering with auto-population.
- **Streaming iteration**: `find_iter()` provides async generator pagination for large result sets without loading everything into memory.
- **Get-or-create**: `store.get_or_create()` upsert pattern for entities.
- **Async-first architecture**: Built for `async`/`await` throughout with native support for concurrent operations.
- **Full Stash API coverage**: Complete CRUD operations for all entity types, job management, metadata operations, and real-time subscriptions.

---

### Quick Example

```python
import asyncio

from stash_graphql_client import StashContext
from stash_graphql_client.types import UNSET, Scene


async def main():
    context = StashContext(conn={"Host": "localhost", "Port": 9999})
    client = context.client

    # Find and update a scene
    scene = await client.find_scene("scene-id")
    scene.rating100 = 95
    # scene.details stays UNSET (no data loaded for it, won't be sent)
    await scene.save(client)  # Only sends rating100

    # Django-style filtering via the context's store
    store = context.store
    top_rated = await store.find(Scene, rating100__gte=90)


asyncio.run(main())
```

---

### Learn More

- **[📚 Full Documentation](https://jakan-kink.github.io/stash-graphql-client/)** - Complete guides and API reference
- **[🎯 Getting Started Guide](https://jakan-kink.github.io/stash-graphql-client/guide/getting-started/)** - Step-by-step tutorials
- **[💡 Usage Patterns](https://jakan-kink.github.io/stash-graphql-client/guide/usage-patterns/)** - Common recipes and best practices
- **[🏗️ Architecture Overview](https://jakan-kink.github.io/stash-graphql-client/guide/overview/)** - Design decisions and comparisons
- **[🔍 API Reference](https://jakan-kink.github.io/stash-graphql-client/api/client/)** - Complete API documentation

---

## Installation

### From PyPI (Recommended)

```bash
pip install stash-graphql-client
```

### With Poetry

```bash
poetry add stash-graphql-client
```

### From Source

```bash
git clone https://github.com/Jakan-Kink/stash-graphql-client.git
cd stash-graphql-client
poetry install
```

**Requirements**: Python 3.12+ • Poetry (for development)

---

## Connection Options

```python
conn = {
    "Scheme": "http",      # or "https"
    "Host": "localhost",   # Stash server host
    "Port": 9999,          # Stash server port
    "ApiKey": "...",       # Optional API key
}
```

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-or-later)**.

See [LICENSE](LICENSE) for the full license text.

This license ensures:

- ✅ Open source code sharing
- ✅ Network use requires source disclosure
- ✅ Compatible with [Stash](https://github.com/stashapp/stash) (also AGPL-3.0)
- ✅ Derivative works must also be AGPL-3.0
