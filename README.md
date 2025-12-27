# stash-graphql-client

[![PyPI version](https://badge.fury.io/py/stash-graphql-client.svg)](https://badge.fury.io/py/stash-graphql-client)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![codecov](https://codecov.io/gh/Jakan-Kink/stash-graphql-client/branch/main/graph/badge.svg?token=qtamVrMS5r)](https://codecov.io/gh/Jakan-Kink/stash-graphql-client)

Async Python client for [Stash](https://stashapp.cc) GraphQL API.

## Features

- **Async-first**: Built with `gql` + `HTTPXAsyncTransport` + `WebsocketsTransport`
- **Pydantic types**: All Stash GraphQL schema objects as Pydantic v2 models
- **Identity Map**: Smart caching with read-through and field-aware population
- **UNSET Pattern**: Three-level field system (value, null, UNSET) for precise partial updates
- **UUID4 Auto-generation**: Automatic temporary IDs for new objects
- **Full CRUD**: Operations for all entity types (Scene, Gallery, Performer, Studio, Tag, etc.)
- **Job management**: Metadata scanning, generation, and job status tracking
- **Subscriptions**: GraphQL subscription support for real-time updates
- **Fuzzy Dates**: Support for year-only and year-month date formats (Stash v0.30.0+)

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

### Requirements

- Python 3.12+
- Poetry for development

## Quick Start

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
    tag_obj = Tag(name="My Tag")
    tag = await client.create_tag(tag_obj)
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

## Architecture

This library follows a three-layer architecture:

### 1. **StashClient** - GraphQL Transport Layer

Located in `stash_graphql_client/client/`, the client provides direct access to Stash's GraphQL API through typed mixin methods:

```python
# Direct GraphQL operations
scenes = await client.find_scenes()
performer = await client.create_performer(Performer(name="Alice"))
job_id = await client.metadata_scan()
```

### 2. **Pydantic Types** - Schema/ORM Layer

Located in `stash_graphql_client/types/`, all Stash entities are Pydantic v2 models with:

- **UNSET Pattern**: Three-level field system distinguishes between "set to value", "set to null", and "never touched"
- **UUID4 Auto-generation**: New objects get temporary IDs replaced with server IDs on save
- **Bidirectional Relationships**: Automatic sync between related entities

```python
from stash_graphql_client.types import Scene, UNSET

# Create with partial data - UUID4 auto-generated
scene = Scene(title="My Scene", rating100=85)
print(f"New object ID: {scene.id}")  # UUID4 hex string (32 chars)
print(f"Is new: {scene.is_new()}")   # True

scene.details = UNSET  # Don't touch this field on save

# Save sends only non-UNSET fields
await scene.save(client)
print(f"Server ID: {scene.id}")      # Server-assigned ID
print(f"Is new: {scene.is_new()}")   # False
```

### 3. **StashEntityStore** - Identity Map & Caching Layer

Located in `stash_graphql_client/store.py`, provides SQLAlchemy/ActiveRecord-style data access:

```python
from stash_graphql_client import StashContext

async with StashContext(conn=...) as client:
    store = StashEntityStore(client)

    # Read-through caching
    performer = await store.get(Performer, "123")

    # Field-aware population (load only what you need)
    performer = await store.populate(performer, fields=["scenes", "images"])

    # Get-or-create pattern
    tag = await store.get_or_create(Tag, name="Action")
    await store.save(tag)
```

## Documentation

- **[Quick Reference](docs/reference/quick-reference.md)** - UNSET & UUID4 patterns cheat sheet
- **[UNSET & UUID4 Guide](docs/guide/unset-pattern.md)** - Comprehensive guide with examples
- **[Usage Examples](docs/guide/usage-examples.md)** - ID mapping, hierarchy navigation, convenience methods
- **[Fuzzy Dates Guide](docs/guide/fuzzy-dates.md)** - Working with partial date formats (v0.30.0+)
- **[Bidirectional Relationships](docs/architecture/bidirectional-relationships.md)** - Entity relationship architecture
- **[API Reference](docs/api/)** - Complete API documentation

## Available Operations

### Scenes

- `find_scenes(filter)` - Search scenes with filters
- `find_scene(id)` - Find scene by ID
- `create_scene(scene)` - Create new scene
- `update_scene(scene)` - Update scene details
- `destroy_scene(id)` - Delete scene

### Galleries

- `find_galleries(filter)` - Search galleries with filters
- `find_gallery(id)` - Find gallery by ID
- `create_gallery(gallery)` - Create new gallery
- `update_gallery(gallery)` - Update gallery details
- `destroy_gallery(id)` - Delete gallery

### Images

- `find_images(filter)` - Search images with filters
- `find_image(id)` - Find image by ID
- `update_image(image)` - Update image details
- `destroy_image(id)` - Delete image

### Performers

- `find_performers(filter)` - Search performers with filters
- `find_performer(id)` - Find performer by ID
- `map_performer_ids(performers, create)` - Convert performer names/objects to IDs
- `all_performers()` - Get all performers (deprecated, use find_performers)
- `create_performer(performer)` - Create new performer
- `update_performer(performer)` - Update performer details
- `bulk_performer_update(input)` - Update multiple performers
- `destroy_performer(id)` - Delete performer

### Studios

- `find_studios(filter)` - Search studios with filters
- `find_studio(id)` - Find studio by ID
- `find_studio_hierarchy(id)` - Get full parent chain from root to studio
- `find_studio_root(id)` - Find the top-level parent studio
- `map_studio_ids(studios, create)` - Convert studio names/objects to IDs
- `create_studio(studio)` - Create new studio
- `update_studio(studio)` - Update studio details
- `bulk_studio_update(input)` - Update multiple studios
- `studio_destroy(id)` - Delete studio

### Tags

- `find_tags(filter)` - Search tags with filters
- `find_tag(id)` - Find tag by ID
- `map_tag_ids(tags, create)` - Convert tag names/objects to IDs
- `create_tag(tag)` - Create new tag
- `update_tag(tag)` - Update tag details
- `tags_merge(source, destination)` - Merge tags
- `bulk_tag_update(input)` - Update multiple tags
- `destroy_tag(id)` - Delete tag

### Groups (formerly Movies)

- `find_groups(filter)` - Search groups with filters
- `find_group(id)` - Find group by ID
- `create_group(group)` - Create new group
- `update_group(group)` - Update group details
- `destroy_group(id)` - Delete group

### Markers

- `find_scene_markers(filter)` - Search scene markers
- `find_scene_marker(id)` - Find marker by ID
- `create_scene_marker(marker)` - Create new marker
- `update_scene_marker(marker)` - Update marker
- `destroy_scene_marker(id)` - Delete marker

### System Operations

- `get_system_status()` - Get current system status
- `check_system_ready()` - Verify system is ready for processing
- `stats()` - Get database statistics
- `version()` - Get Stash version information
- `latestversion()` - Get latest available Stash version
- `logs()` - Get system logs
- `directory(path, locale)` - Browse filesystem
- `dlna_status()` - Get DLNA server status
- `sql_query(sql, args)` - Execute SQL query (⚠️ DANGEROUS - use with caution)
- `sql_exec(sql, args)` - Execute SQL statement (⚠️ DANGEROUS - use with caution)
- `get_configuration()` - Get complete configuration

### Configuration Operations

- `configure_general(input)` - Configure general Stash settings
- `configure_interface(input)` - Configure Stash interface settings
- `configure_dlna(input)` - Configure DLNA server settings
- `configure_defaults(input)` - Configure default metadata operation settings
- `configure_ui(input, partial)` - Configure UI settings
- `configure_ui_setting(key, value)` - Configure a single UI setting
- `configure_scraping(input)` - Configure scraping settings
- `generate_api_key(input)` - Generate a new API key
- `find_saved_filter(id)` - Find a saved filter by ID
- `find_saved_filters(mode)` - Find all saved filters
- `validate_stashbox_credentials(input)` - Validate StashBox credentials
- `enable_dlna(input)` - Enable DLNA server
- `disable_dlna(input)` - Disable DLNA server
- `add_temp_dlna_ip(input)` - Add temporary DLNA IP whitelist
- `remove_temp_dlna_ip(input)` - Remove temporary DLNA IP from whitelist

### Metadata Operations

- `metadata_scan(options, input)` - Scan for new/updated files
- `metadata_generate(options, input)` - Generate metadata (covers, sprites, previews, etc.)
- `metadata_clean(options, input)` - Clean metadata
- `metadata_clean_generated(input)` - Clean generated files
- `metadata_auto_tag(input)` - Auto-tag entities
- `metadata_identify(input)` - Identify entities via scrapers
- `metadata_import(input)` - Import metadata from JSON
- `metadata_export(input)` - Export metadata to JSON
- `get_configuration_defaults()` - Get default configuration settings

### Migration & Database Operations

- `migrate(input)` - Run database migration
- `migrate_hash_naming()` - Migrate to new hash naming scheme
- `migrate_scene_screenshots(input)` - Migrate scene screenshots
- `migrate_blobs(input)` - Migrate binary data to new storage
- `anonymise_database(input)` - Anonymize database for sharing
- `optimise_database()` - Optimize database performance
- `backup_database(input)` - Create database backup

### Plugin Operations

- `get_plugins()` - Get all loaded plugins
- `get_plugin_tasks()` - Get available plugin tasks
- `set_plugins_enabled(plugins, enabled)` - Enable/disable plugins
- `reload_plugins()` - Reload all plugins
- `run_plugin_task(plugin_id, task_name, args)` - Run plugin task
- `run_plugin_operation(plugin_id, args)` - Run plugin operation
- `configure_plugin(plugin_id, input)` - Configure plugin settings

### Package Operations

- `installed_packages(type)` - Get installed packages
- `available_packages(type, source)` - Get available packages
- `install_packages(type, packages)` - Install packages
- `update_packages(type, packages)` - Update packages
- `uninstall_packages(type, packages)` - Uninstall packages

### Job Operations

- `find_job(id)` - Find job by ID
- `stop_job(id)` - Stop running job
- `wait_for_job(id)` - Wait for job to complete (async)

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
performer = Performer(name="John Doe", birthdate="1990")  # Year-only birthdate
await client.create_performer(performer)

scene_data = {
    "date": "2024-03",  # Month precision
}
```

Supported date formats:

- `YYYY` - Year precision (e.g., "2024")
- `YYYY-MM` - Month precision (e.g., "2024-03")
- `YYYY-MM-DD` - Day precision (e.g., "2024-03-15")

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-or-later)**.

See [LICENSE](LICENSE) for the full license text.

This license ensures:

- ✅ Open source code sharing
- ✅ Network use requires source disclosure
- ✅ Compatible with [Stash](https://github.com/stashapp/stash) (also AGPL-3.0)
- ✅ Derivative works must also be AGPL-3.0
