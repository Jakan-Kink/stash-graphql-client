# Types

Type definitions and utilities for Stash entities.

## Base Types

::: stash_graphql_client.types.base.StashObject
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.base.StashInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.base.StashResult
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Core Entity Types

::: stash_graphql_client.types.scene.Scene
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.performer.Performer
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.gallery.Gallery
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.image.Image
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.group.Group
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.studio.Studio
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.tag.Tag
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.markers.SceneMarker
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## UNSET Pattern

::: stash_graphql_client.types.unset.UnsetType
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: stash_graphql_client.types.unset.UNSET
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Date Utilities

::: stash_graphql_client.types.date_utils.FuzzyDate
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.date_utils.DatePrecision
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.date_utils.validate_fuzzy_date
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.date_utils.normalize_date
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Enums

::: stash_graphql_client.types.enums
    options:
      show_root_heading: false
      show_source: false
      members: true
      heading_level: 3

## File Types

::: stash_graphql_client.types.files.VideoFile
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.files.ImageFile
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.files.GalleryFile
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.files.BaseFile
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.files.Folder
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Input Types

Input types for mutations (create, update, destroy operations).

::: stash_graphql_client.types.scene.SceneCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.scene.SceneUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.performer.PerformerCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.performer.PerformerUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.gallery.GalleryCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.gallery.GalleryUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.group.GroupCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.group.GroupUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.studio.StudioCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.studio.StudioUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.tag.TagCreateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.tag.TagUpdateInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Filter Types

::: stash_graphql_client.types.filters.SceneFilterType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.filters.PerformerFilterType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.filters.GalleryFilterType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.filters.ImageFilterType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Result Types

::: stash_graphql_client.types.scene.FindScenesResultType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.performer.FindPerformersResultType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.gallery.FindGalleriesResultType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.image.FindImagesResultType
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Job Types

::: stash_graphql_client.types.job.Job
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.job.JobStatus
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Configuration Types

::: stash_graphql_client.types.config.ConfigResult
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.config.StashConfig
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Metadata Types

::: stash_graphql_client.types.metadata.ScanMetadataInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.metadata.GenerateMetadataInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.metadata.AutoTagMetadataInput
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Plugin Types

::: stash_graphql_client.types.plugin.Plugin
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.plugin.PluginTask
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Package Types

::: stash_graphql_client.types.package.Package
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Scraper Types

::: stash_graphql_client.types.scraped_types.Scraper
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.scraped_types.ScrapedScene
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.scraped_types.ScrapedPerformer
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## StashBox Types

::: stash_graphql_client.types.stashbox.StashBox
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Logging Types

::: stash_graphql_client.types.logging.LogEntry
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.logging.LogLevel
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Version Types

::: stash_graphql_client.types.version.Version
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

::: stash_graphql_client.types.version.LatestVersion
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
