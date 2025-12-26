# Stash GraphQL Client

**Async Python client for [Stash](https://stashapp.cc) GraphQL API**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## Overview

`stash-graphql-client` is a modern, type-safe Python library for interacting with Stash media server's GraphQL API. Built with async-first architecture and comprehensive Pydantic type definitions, it provides a robust foundation for automating and extending your Stash instance.

## Key Features

- **🚀 Async-first**: Built on `gql` with `HTTPXAsyncTransport` and `WebsocketsTransport`
- **📝 Fully Typed**: All Stash GraphQL schema objects as Pydantic v2 models
- **🔄 Complete CRUD**: Operations for scenes, galleries, performers, studios, tags, and more
- **⚙️ Job Management**: Metadata scanning, generation, and real-time job status tracking
- **📡 Subscriptions**: GraphQL subscription support for live updates
- **🎯 Identity Map**: Built-in caching for efficient object reuse and relationship navigation
- **📅 Fuzzy Dates**: First-class support for Stash v0.30.0+ partial date formats

## Quick Example

```python
from stash_graphql_client import StashClient, StashContext
from stash_graphql_client.types import Tag

# Using context manager (recommended)
async with StashContext(conn={
    "Host": "localhost",
    "Port": 9999,
    "ApiKey": "your-api-key",  # Optional
}) as client:
    # Find all studios
    result = await client.find_studios()
    print(f"Found {result.count} studios")

    # Create a new tag
    tag = await client.create_tag(Tag(name="My Tag"))
    print(f"Created tag: {tag.name}")
```

## What Makes This Different?

### Identity Map Pattern

Same entity IDs return the same object reference across all queries, ensuring data consistency:

```python
scene1 = Scene.from_dict({"id": "123", "title": "Test"})
scene2 = Scene.from_dict({"id": "123", "title": "Test"})
assert scene1 is scene2  # Same cached object!
```

### UNSET Sentinel

Distinguish between unqueried fields, null values, and actual data:

```python
from stash_graphql_client.types import UNSET

scene.title = "Test"   # Set to value
scene.title = None     # Explicitly null
scene.title = UNSET    # Never queried
```

### Fuzzy Date Support

Work with partial dates just like Stash v0.30.0+:

```python
from stash_graphql_client.types import FuzzyDate

date = FuzzyDate("2024-03")  # Year-month precision
print(date.precision)  # DatePrecision.MONTH
```

## Who Should Use This?

This library is perfect for:

- **Automation**: Build scripts to organize and manage your Stash library
- **Integration**: Connect Stash with other tools and services
- **Extensions**: Create custom workflows and plugins
- **Analysis**: Extract and analyze metadata from your collection
- **Testing**: Programmatically interact with Stash for testing purposes

## Next Steps

<div class="grid cards" markdown>

- :material-book-open-variant:{ .lg .middle } **User Guide**

    ---

    Learn core concepts and patterns

    [:octicons-arrow-right-24: UNSET Pattern](guide/unset-pattern.md)

- :material-code-tags:{ .lg .middle } **API Reference**

    ---

    Comprehensive API documentation

    [:octicons-arrow-right-24: API Docs](api/client.md)

- :material-calendar:{ .lg .middle } **Fuzzy Dates**

    ---

    Work with partial dates

    [:octicons-arrow-right-24: Date Utilities](guide/fuzzy-dates.md)

</div>

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-or-later)**.

See [LICENSE](https://github.com/Jakan-Kink/stash-graphql-client/blob/main/LICENSE) for the full license text.

This license ensures:

- ✅ Open source code sharing
- ✅ Network use requires source disclosure
- ✅ Compatible with [Stash](https://github.com/stashapp/stash) (also AGPL-3.0)
- ✅ Derivative works must also be AGPL-3.0
