"""Primary-file assignment and file_ids create wiring (Scene/Gallery/Image).

Covers:
- set_primary_file reorders the file collection primary-first and marks only
  primary_file_id dirty (the reorder is re-baselined, not a pending change).
- Scene.files maps to SceneCreateInput.file_ids on create (first id = primary).
- primary_file_id flows to *UpdateInput.primary_file_id on update; file_ids is
  dropped from update payloads and primary_file_id from create payloads by the
  per-operation _filter_input_fields routing.
- Reverse file relationships (VideoFile.scenes etc.) and the Gallery/Image file
  lists stay read-only (no file_ids input exists for them).
"""

import pytest

from stash_graphql_client.types import UNSET, Scene
from stash_graphql_client.types.files import (
    GalleryFile,
    ImageFile,
    VideoFile,
)
from stash_graphql_client.types.gallery import Gallery
from stash_graphql_client.types.image import Image
from stash_graphql_client.types.scene import SceneCreateInput
from stash_graphql_client.types.tag import Tag


@pytest.mark.usefixtures("mock_entity_store")
class TestSetPrimaryFile:
    """set_primary_file behavior across the file-bearing entity types."""

    def test_reorders_primary_first_and_only_primary_id_dirty(self):
        scene = Scene(id="123", title="t", organized=False, urls=[])
        scene.files = [VideoFile(id="901"), VideoFile(id="902"), VideoFile(id="903")]
        scene.mark_clean()

        scene.set_primary_file("903")

        assert [f.id for f in scene.files] == ["903", "901", "902"]
        assert set(scene.get_changed_fields()) == {"primary_file_id"}
        assert scene.primary_file_id == "903"

    def test_accepts_file_object(self):
        target = VideoFile(id="902")
        scene = Scene(id="123", title="t", organized=False, urls=[])
        scene.files = [VideoFile(id="901"), target]

        scene.set_primary_file(target)

        assert scene.files[0] is target
        assert scene.primary_file_id == "902"

    def test_invalid_member_raises(self):
        scene = Scene(id="123", title="t", organized=False, urls=[])
        scene.files = [VideoFile(id="901")]

        with pytest.raises(ValueError, match="not among"):
            scene.set_primary_file("999")

    def test_empty_file_raises(self):
        scene = Scene(id="123", title="t")

        with pytest.raises(ValueError, match="requires a file"):
            scene.set_primary_file("")

    def test_unloaded_collection_sets_id_without_reorder(self):
        scene = Scene(id="123", title="t")  # files UNSET (not loaded)

        scene.set_primary_file("903")

        assert scene.primary_file_id == "903"
        assert scene.files is UNSET

    @pytest.mark.asyncio
    async def test_gallery_reorders_files_and_serializes_primary(self):
        gallery = Gallery(id="500", title="g")
        gallery.files = [GalleryFile(id="801"), GalleryFile(id="802")]
        gallery.mark_clean()

        gallery.set_primary_file("802")

        assert [f.id for f in gallery.files] == ["802", "801"]
        assert set(gallery.get_changed_fields()) == {"primary_file_id"}
        data = await gallery.to_input()
        assert data["primary_file_id"] == "802"
        assert "file_ids" not in data  # galleries have no file_ids input

    @pytest.mark.asyncio
    async def test_image_reorders_visual_files_and_serializes_primary(self):
        image = Image(id="600")
        image.visual_files = [ImageFile(id="701"), ImageFile(id="702")]
        image.mark_clean()

        image.set_primary_file("702")

        assert [f.id for f in image.visual_files] == ["702", "701"]
        assert set(image.get_changed_fields()) == {"primary_file_id"}
        data = await image.to_input()
        assert data["primary_file_id"] == "702"

    def test_base_entity_without_files_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            Tag(id="1").set_primary_file("x")


@pytest.mark.usefixtures("mock_entity_store")
class TestFileIdsCreateRouting:
    """to_input routes file fields per operation (create vs update)."""

    @pytest.mark.asyncio
    async def test_create_maps_files_to_file_ids_primary_first(self, monkeypatch):
        # Scene creation is intentionally guarded; opt in like the integration
        # fixture does, then verify files serialize to file_ids in order.
        monkeypatch.setattr(Scene, "__create_input_type__", SceneCreateInput)
        scene = Scene(title="new", urls=["https://example.com/s"], organized=True)
        scene.files = [VideoFile(id="903"), VideoFile(id="901")]

        data = await scene.to_input()

        assert data["file_ids"] == ["903", "901"]
        assert "primary_file_id" not in data  # not on SceneCreateInput

    @pytest.mark.asyncio
    async def test_update_emits_primary_file_id_not_file_ids(self):
        scene = Scene(id="123", title="t", organized=False, urls=[])
        scene.files = [VideoFile(id="901"), VideoFile(id="902")]
        scene.mark_clean()

        scene.set_primary_file("902")
        data = await scene.to_input()

        assert data["primary_file_id"] == "902"
        assert "file_ids" not in data  # not on SceneUpdateInput

    @pytest.mark.asyncio
    async def test_update_drops_file_set_rewrite(self):
        # The file set is not assignable on update; a direct files rewrite is
        # dropped (SceneUpdateInput has no file_ids) rather than sent.
        scene = Scene(id="123", title="t", organized=False, urls=[])
        scene.files = [VideoFile(id="901")]
        scene.mark_clean()

        scene.files = [VideoFile(id="901"), VideoFile(id="902")]
        data = await scene.to_input()

        assert "file_ids" not in data


class TestFileRelationshipMetadata:
    """Read/write sidedness of the file relationships after the habtm fix."""

    def test_scene_files_is_writable_to_file_ids(self):
        meta = Scene.__relationships__["files"]
        assert meta.target_field == "file_ids"
        assert meta.query_field == "files"
        assert meta.query_strategy == "direct_field"

    def test_gallery_and_image_file_lists_remain_read_only(self):
        # No file_ids input exists for galleries/images — lists are read-only.
        assert Gallery.__relationships__["files"].target_field == ""
        assert Image.__relationships__["visual_files"].target_field == ""

    def test_reverse_file_resolvers_remain_read_only(self):
        # The #6938 reverse resolvers (file -> entities) are read-only.
        assert VideoFile.__relationships__["scenes"].target_field == ""
        assert ImageFile.__relationships__["images"].target_field == ""
        assert GalleryFile.__relationships__["galleries"].target_field == ""
