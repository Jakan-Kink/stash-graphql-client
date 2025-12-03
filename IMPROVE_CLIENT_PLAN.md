# Stash GraphQL Client Implementation Plan

## Implementation Status ✅

**As of December 3, 2025:**

- **Steps 1-9 and 11: COMPLETE** ✅
- **Step 10: INCOMPLETE** ⚠️ (fragment field completeness)
- **Additional operations discovered** during schema inspection (not in original plan)

### Comprehensive Schema Analysis Results

**Total GraphQL Operations in Schema:**

- Queries: ~48 operations
- Mutations: ~143 operations
- Subscriptions: 3 operations

**Implementation Coverage (excluding out-of-scope):**

- ✅ **Core entity CRUD**: ~95% complete (Scene, Performer, Studio, Tag, Image, Gallery, Group, File)
- ✅ **Deletion operations**: 100% complete
- ✅ **Bulk operations**: 100% complete
- ✅ **File/folder operations**: 100% complete
- ✅ **Metadata operations**: ~85% complete (missing full import/export, auto-tag)
- ✅ **Configuration**: 100% complete
- ✅ **Migration utilities**: 100% complete
- ⚠️ **System utilities**: ~40% complete (missing job queue management, system status, logs)
- ⚠️ **Fragment completeness**: ~60% complete (many fields available but not fetched)

### Completed Features

✅ **Step 1:** Version queries (`version`, `latestversion`)
✅ **Step 2:** All deletion operations (scenes, performers, studios, tags, images, markers, files)
✅ **Step 3:** File/folder operations (`find_folder`, `find_folders`, `FolderFilterType`)
✅ **Step 4:** Filter types (`FileFilterType`, `VideoFileFilterInput`, `ImageFileFilterInput`, `FingerprintFilterInput`)
✅ **Step 5:** Bulk updates (performers, studios, images, scene markers, groups)
✅ **Step 6:** Scene management (`scene_merge`, `scene_assign_file`)
✅ **Step 7:** Metadata operations (clean, export objects, import objects, backup, anonymise)
✅ **Step 8:** Migration utilities (migrate, migrate_hash_naming, migrate_scene_screenshots, migrate_blobs)
✅ **Step 9:** Configuration mutations (general, interface, DLNA, defaults, UI, API keys)
✅ **Step 11:** Group CRUD operations (all methods + sub-group management)

### Remaining Work

⚠️ **Step 10:** Fragment field completeness - Add missing fields to query fragments

⚠️ **Additional operations:** Job management, system utilities, and other operations discovered during schema analysis (detailed below)

---

## Additional Missing Operations (Not in Original Plan)

### System & Utility Operations

**Query Operations:**

- `directory(path: String, locale: String): Directory!` - File system browser
- `allPerformers: [Performer!]!` - Non-paginated performer list
- `systemStatus: SystemStatus!` - System status information
- `jobQueue: [Job!]` - List all queued/running jobs (only `find_job` exists)
- `logs: [LogEntry!]!` - System logs query

**Mutation Operations:**

- `stopJob(job_id: ID!): Boolean!` - Cancel a running job
- `stopAllJobs: Boolean!` - Cancel all jobs
- `optimiseDatabase: ID!` - Optimize database (returns job ID)

**Metadata Operations (core, non-scraper):**

- `metadataImport: ID!` - Full metadata import (stub exists)
- `metadataExport: ID!` - Full metadata export (stub exists)
- `metadataAutoTag(input: AutoTagMetadataInput!): ID!` - Auto-tag operation (stub exists)

**Gallery Operation:**

- `bulkGalleryUpdate(input: BulkGalleryUpdateInput!): [Gallery!]` - Bulk gallery updates (stub exists)

**Deprecated Query Operations (present but may not need implementation):**

- `allSceneMarkers: [SceneMarker!]!` - Use `findSceneMarkers` instead

**Wall Queries (utility features in not_implemented):**

- `marker_wall(q: String): [SceneMarker!]!`
- `marker_strings(q: String, sort: String): [MarkerStringsResultType]!`

**Other Operations (in not_implemented):**

- `scene_streams(id: String): [SceneStreamEndpoint!]!` - Get stream endpoints for a scene

### Priority Assessment

**High Priority:**

- `jobQueue`, `stopJob`, `stopAllJobs` - Essential for job management
- `systemStatus` - Important system monitoring
- `bulkGalleryUpdate` - Completes CRUD operations
- `optimiseDatabase` - Database maintenance

**Medium Priority:**

- `directory` - File browsing capability
- `logs` - Debugging and monitoring
- `metadataImport`, `metadataExport` - Full import/export (partial already exists)
- `metadataAutoTag` - Content tagging

**Low Priority:**

- `allPerformers` - Convenience, `findPerformers` works
- `marker_wall`, `marker_strings` - UI convenience features
- `scene_streams` - May be redundant with existing scene stream support

---

---

## Out of Scope (Do Not Implement)

The following features are explicitly excluded from this implementation plan:

- ❌ **Activity Tracking Operations** (play history, O-counters for scenes/images)
- ❌ **Scraper Functionality** (all scraped content types and scraper operations)
  - `listScrapers`, `scrapeSingle*`, `scrapeMulti*`, `scrape*URL`
  - `reloadScrapers`, `configureScraping`
  - `metadataIdentify` (uses scrapers)
- ❌ **Plugin System** (plugin types, operations, and management)
  - `plugins`, `pluginTasks`, `runPluginTask`, `runPluginOperation`
  - `reloadPlugins`, `setPluginsEnabled`, `configurePlugin`
- ❌ **Package Management** (package types and operations)
  - `installedPackages`, `availablePackages`
  - `installPackages`, `updatePackages`, `uninstallPackages`
- ❌ **Stats** (statistics query and types)
  - `stats` query
- ❌ **StashBox Integration** (StashBox-specific operations and types)
  - `validateStashBoxCredentials`, `submitStashBox*`
  - `stashBoxBatch*`
- ❌ **Saved/Default Filters** (UI state management)
  - `findSavedFilter`, `findSavedFilters`, `findDefaultFilter`
  - `saveFilter`, `destroySavedFilter`, `setDefaultFilter`
- ❌ **System Setup Operations** (one-time initialization)
  - `setup` mutation
  - `downloadFFMpeg` mutation

---

## Remaining Implementation Work

### Step 10: Fragment Field Completeness

**Status:** ⏸️ Deferred - Revisit after evaluating actual performance needs

**Original Goal:** Add missing fields to fragments so queries return complete objects

**Current Assessment:** Most missing fields are:

- Expensive resolvers (counts, o_counter) that slow queries
- Nested relationships that may not always be needed
- Fields that are out-of-scope (play_history, o_history)

**Approach:** Keep fragments lean for now. If specific use cases need additional fields, add them selectively rather than all at once.

**Fields identified but not yet added:**

1. **Scene:** `director`, `rating100`, `organized`, `interactive`, `interactive_speed`, `last_played_at`, `resume_time`, `play_duration`, `play_count`, `scene_markers`, `galleries`, `groups`
2. **Performer:** `weight`, `rating100`, `death_date`, `favorite`, `ignore_auto_tag`, `height_cm`, `career_length`, `custom_fields`, resolver counts
3. **Studio:** `child_studios`, `groups`, `o_counter`, `stash_ids`, `rating100`, `favorite`, `ignore_auto_tag`, resolver counts
4. **Tag:** `sort_name`, `favorite`, `ignore_auto_tag`, resolver counts
5. **Image:** `rating100`
6. **Marker:** `end_seconds`, `stream`, `preview`, `screenshot`
7. **Gallery:** `rating100`, `folder`, `chapters`, `cover`, `image_count`
8. **Group:** `aliases`, `duration`, `rating100`, `director`, `synopsis`, `containing_groups`, `sub_groups`, resolver counts

**Decision:** Focus on high-priority missing operations first (job management, system utilities). Fragment completeness can be addressed incrementally based on actual user needs.

**Effort:** Low (1-2 days if needed)

---

### Additional Missing Operations (Discovered During Schema Analysis)

#### High Priority

**Job Management:**

- `jobQueue: [Job!]` - List all queued/running jobs (only `find_job` exists)
- `stopJob(job_id: ID!): Boolean!` - Cancel a running job
- `stopAllJobs: Boolean!` - Cancel all jobs

**Gallery:**

- `bulkGalleryUpdate(input: BulkGalleryUpdateInput!): [Gallery!]` - Bulk gallery updates (stub exists in not_implemented)

**Database:**

- `optimiseDatabase: ID!` - Optimize database (returns job ID)

#### Medium Priority

**System & Monitoring:**

- `systemStatus: SystemStatus!` - System status information
- `directory(path: String, locale: String): Directory!` - File system browser
- `logs: [LogEntry!]!` - System logs query

**Metadata Operations (stubs exist):**

- `metadataImport: ID!` - Full metadata import
- `metadataExport: ID!` - Full metadata export
- `metadataAutoTag(input: AutoTagMetadataInput!): ID!` - Auto-tag operation

#### Low Priority (Utility/Convenience)

- `allPerformers: [Performer!]!` - Non-paginated performer list (deprecated style, `findPerformers` works)
- `marker_wall(q: String): [SceneMarker!]!` - UI convenience
- `marker_strings(q: String, sort: String): [MarkerStringsResultType]!` - UI convenience
- `scene_streams(id: String): [SceneStreamEndpoint!]!` - Get stream endpoints for a scene
- `allSceneMarkers: [SceneMarker!]!` - Deprecated, use `findSceneMarkers` instead

---

## Notes

- All implementations follow existing code patterns in the client
- Use Pydantic models for type safety
- Add proper error handling and logging
- Update type exports in `types/__init__.py` as needed
- Follow existing naming conventions (snake_case for methods, PascalCase for classes)

**Phase 1 Complete:**

- Version queries functional
- All deletion operations working
- File/folder operations complete
- Missing filter types implemented

**Phase 2 Complete:**

- All bulk update operations working
- Scene merge and file assignment functional

**Phase 3 Complete:**

- Metadata operations implemented
- Migration utilities available
- Configuration mutations working

**Phase 4 Complete:**

- All fragments fetch complete data
- Group CRUD operations available

**Final Coverage Target:**

- Queries: 40+/48 implemented (~83%)
- Mutations: 95+/143 implemented (~66%)
- Subscriptions: 3/3 implemented (100%)
- **Overall: ~70% coverage** (excluding out-of-scope features)

---

## Notes

- All implementations should follow existing code patterns in the client
- Use Pydantic models for type safety
- Add proper error handling and logging
- Update type exports in `types/__init__.py` as needed
- Follow existing naming conventions (snake_case for methods, PascalCase for classes)
