⏺ Usage Examples for New Convenience Methods

1. Entity ID Mapping - Simplified Workflows

Before (without convenience methods):

# Old way - lots of boilerplate

async def create_scene_with_tags(client, scene_data):
tag_ids = []
for tag_name in ["Action", "Drama", "Thriller"]:
results = await client.find_tags(
tag_filter={"name": {"value": tag_name, "modifier": "EQUALS"}}
)
if results.count > 0:
tag_ids.append(results.tags[0].id)
else: # Create missing tag
new_tag = await client.create_tag(Tag(name=tag_name))
tag_ids.append(new_tag.id)

      scene = Scene(title="My Scene", tag_ids=tag_ids)
      return await client.create_scene(scene)

After (with map_tag_ids()):

# New way - clean and simple

async def create_scene_with_tags(client, scene_data):
tag_ids = await client.map_tag_ids(
["Action", "Drama", "Thriller"],
create=True # Auto-create missing tags
)

      scene = Scene(title="My Scene", tag_ids=tag_ids)
      return await client.create_scene(scene)

---

2. Studio Hierarchy Navigation

Finding Root Studios:

# Scenario: You have a child studio and want to find the root parent

studio_id = "child-studio-123"

# Get the full hierarchy (root to child)

hierarchy = await client.find_studio_hierarchy(studio_id)

# Returns: [<Root Studio>, <Parent Studio>, <Child Studio>]

print(f"Root: {hierarchy[0].name}")
print(f"Direct parent: {hierarchy[-2].name}")
print(f"Current: {hierarchy[-1].name}")

# Or just get the root directly

root = await client.find_studio_root(studio_id)
print(f"Root studio: {root.name}")

Practical Use Case - Organizing by Root Studio:

# Group all scenes by their root studio

async def group_scenes_by_root_studio(client, scene_ids):
root_groups = {}

      for scene_id in scene_ids:
          scene = await client.find_scene(scene_id)
          if scene.studio:
              root = await client.find_studio_root(scene.studio.id)
              root_name = root.name if root else "Unknown"

              if root_name not in root_groups:
                  root_groups[root_name] = []
              root_groups[root_name].append(scene)

      return root_groups

---

3. Performer Mapping with Alias Support

Basic Performer Mapping:

# Map performer names to IDs (includes alias search)

performer_ids = await client.map_performer_ids(
["Jane Doe", "John Smith", "AliasName"],
create=True
)

# Use in scene creation

scene = Scene(
title="Scene Title",
performer_ids=performer_ids
)
await client.create_scene(scene)

Handling Multiple Matches:

from stash_graphql_client.types import OnMultipleMatch

# Skip ambiguous matches

performer_ids = await client.map_performer_ids(
["Common Name"], # Might match multiple performers
on_multiple=OnMultipleMatch.RETURN_NONE # Skip if ambiguous
)

# Or return first match with warning

performer_ids = await client.map_performer_ids(
["Common Name"],
on_multiple=OnMultipleMatch.RETURN_FIRST # Use first match (default)
)

---

4. Batch Scene Creation with Mixed Entity Types

Complex Real-World Example:

async def create_scene_from_metadata(client, metadata):
"""Create a scene from scraped metadata with automatic entity resolution."""

      # Map all entity names to IDs in parallel
      tag_ids = await client.map_tag_ids(
          metadata.get("tags", []),
          create=True
      )

      performer_ids = await client.map_performer_ids(
          metadata.get("performers", []),
          create=True,
          on_multiple=OnMultipleMatch.RETURN_FIRST
      )

      studio_ids = await client.map_studio_ids(
          [metadata.get("studio")],
          create=True
      )

      # Create scene with all relationships resolved
      scene = Scene(
          title=metadata["title"],
          details=metadata.get("details"),
          date=metadata.get("date"),
          tag_ids=tag_ids,
          performer_ids=performer_ids,
          studio_id=studio_ids[0] if studio_ids else None
      )

      return await client.create_scene(scene)

---

5. Studio Hierarchy Analysis

Find All Root Studios:

async def find_all_root_studios(client):
"""Find all root studios in the database."""
all_studios = await client.find_studios()
root_studios = []

      for studio in all_studios.studios:
          hierarchy = await client.find_studio_hierarchy(studio.id)
          root = hierarchy[0] if hierarchy else None
          if root and root.id == studio.id:  # This studio is a root
              root_studios.append(studio)

      return root_studios

Build Studio Tree:

async def get_studio_tree_depth(client, studio_id):
"""Get the depth of a studio in the hierarchy."""
hierarchy = await client.find_studio_hierarchy(studio_id)
return len(hierarchy) - 1 # 0 = root, 1 = child, 2 = grandchild, etc.

# Example usage

depth = await get_studio_tree_depth(client, "studio-123")
print(f"Studio is {depth} levels deep in the hierarchy")

---

6. Bulk Operations with Auto-Creation

Importing from External Source:

async def import_scenes_from_csv(client, csv_data):
"""Import scenes from CSV with automatic entity creation."""
created_scenes = []

      for row in csv_data:
          # Parse CSV row
          tag_names = row["tags"].split(",")
          performer_names = row["performers"].split(",")
          studio_name = row["studio"]

          # Map everything with auto-creation
          tag_ids = await client.map_tag_ids(tag_names, create=True)
          performer_ids = await client.map_performer_ids(performer_names, create=True)
          studio_ids = await client.map_studio_ids([studio_name], create=True)

          # Create scene
          scene = Scene(
              title=row["title"],
              tag_ids=tag_ids,
              performer_ids=performer_ids,
              studio_id=studio_ids[0] if studio_ids else None
          )

          created_scene = await client.create_scene(scene)
          created_scenes.append(created_scene)

      return created_scenes

---
