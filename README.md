# stash-graphql-client

Async Python client for [Stash](https://stashapp.cc) GraphQL API.

## Features

- **Async-first**: Built with `gql` + `HTTPXAsyncTransport` + `WebsocketsTransport`
- **Pydantic types**: All Stash GraphQL schema objects as Pydantic models
- **Full CRUD**: Operations for all entity types (Scene, Gallery, Performer, Studio, Tag, etc.)
- **Job management**: Metadata scanning, generation, and job status tracking
- **Subscriptions**: GraphQL subscription support for real-time updates

## Installation

```bash
# From AWS CodeArtifact (private)
pip install stash-graphql-client

# Or with Poetry
poetry add stash-graphql-client
```

## Quick Start

```python
from stash_graphql_client import StashClient, StashContext

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
    tag = await client.create_tag(name="My Tag")
    print(f"Created tag: {tag.name}")

# Or manual lifecycle management
context = StashContext(conn={"Host": "localhost", "Port": 9999})
client = await context.get_client()
try:
    scenes = await client.find_scenes()
finally:
    await context.close()
```

## Connection Options

```python
conn = {
    "Scheme": "http",      # or "https"
    "Host": "localhost",   # Stash server host
    "Port": 9999,          # Stash server port
    "ApiKey": "...",       # Optional API key
}
```

## Available Operations

### Scenes

- `find_scenes()`, `find_scene(id)`, `create_scene()`, `update_scene()`, `destroy_scene()`

### Galleries

- `find_galleries()`, `find_gallery(id)`, `create_gallery()`, `update_gallery()`, `destroy_gallery()`

### Performers

- `find_performers()`, `find_performer(id)`, `create_performer()`, `update_performer()`, `destroy_performer()`

### Studios

- `find_studios()`, `find_studio(id)`, `create_studio()`, `update_studio()`, `destroy_studio()`

### Tags

- `find_tags()`, `find_tag(id)`, `create_tag()`, `update_tag()`, `destroy_tag()`

### Metadata Operations

- `metadata_scan()` - Scan for new media
- `metadata_generate()` - Generate thumbnails, previews, etc.
- `find_job()`, `wait_for_job()` - Job status tracking

## Fuzzy Date Support (Stash v0.30.0+)

Stash v0.30.0 introduced support for partial dates (year-only or year-month formats) in addition to full dates. This client includes utilities to work with these "fuzzy" dates:

```python
from stash_graphql_client.types import (
    FuzzyDate,
    validate_fuzzy_date,
    normalize_date,
    DatePrecision,
)

# Validate date formats
validate_fuzzy_date("2024")        # True - year only
validate_fuzzy_date("2024-03")     # True - year and month
validate_fuzzy_date("2024-03-15")  # True - full date
validate_fuzzy_date("2024-3")      # False - invalid format

# Create fuzzy dates
date = FuzzyDate("2024-03")
print(date.precision)  # DatePrecision.MONTH
print(date.to_datetime())  # datetime(2024, 3, 1)

# Normalize dates to different precisions
normalize_date("2024-03-15", "year")   # "2024"
normalize_date("2024-03-15", "month")  # "2024-03"
normalize_date("2024", "day")          # "2024-01-01"

# Use in performer/scene data
performer_data = {
    "name": "John Doe",
    "birthdate": "1990",  # Year-only birthdate
}
await client.create_performer(**performer_data)

scene_data = {
    "date": "2024-03",  # Month precision
}
```

Supported date formats:

- `YYYY` - Year precision (e.g., "2024")
- `YYYY-MM` - Month precision (e.g., "2024-03")
- `YYYY-MM-DD` - Day precision (e.g., "2024-03-15")

## License

MIT
