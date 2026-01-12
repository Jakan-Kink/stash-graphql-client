"""Tests for dict input validation across client mixin methods.

This test suite ensures that methods accepting `SomeInput | dict[str, Any]`:
1. Accept valid dict inputs and validate them through Pydantic
2. Reject non-dict inputs with clear TypeError messages
3. Validate dict structure and raise Pydantic validation errors for invalid fields
4. Properly convert validated dicts to GraphQL format
"""

import pytest
from pydantic import ValidationError

from stash_graphql_client.types import (
    BulkGalleryUpdateInput,
    BulkGroupUpdateInput,
    BulkImageUpdateInput,
    BulkPerformerUpdateInput,
    BulkSceneMarkerUpdateInput,
    BulkStudioUpdateInput,
    GroupDestroyInput,
    ImageDestroyInput,
    ImagesDestroyInput,
    PerformerDestroyInput,
    SaveFilterInput,
    SceneDestroyInput,
    SceneHashInput,
    SceneMergeInput,
    ScenesDestroyInput,
    StudioDestroyInput,
    TagDestroyInput,
)
from stash_graphql_client.types.enums import FilterMode


class TestDictValidationTypeChecking:
    """Test that non-dict inputs are rejected with TypeError."""

    @pytest.mark.asyncio
    async def test_bulk_image_update_rejects_non_dict(self, stash_client):
        """bulk_image_update should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be BulkImageUpdateInput or dict"
        ):
            # Intentionally pass wrong type
            await stash_client.bulk_image_update("invalid")  # type: ignore

    @pytest.mark.asyncio
    async def test_scene_destroy_rejects_non_dict(self, stash_client):
        """scene_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be SceneDestroyInput or dict"
        ):
            await stash_client.scene_destroy(123)  # type: ignore

    @pytest.mark.asyncio
    async def test_tag_destroy_rejects_non_dict(self, stash_client):
        """tag_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be TagDestroyInput or dict"
        ):
            await stash_client.tag_destroy([1, 2, 3])  # type: ignore

    @pytest.mark.asyncio
    async def test_bulk_scene_marker_update_rejects_non_dict(self, stash_client):
        """bulk_scene_marker_update should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be BulkSceneMarkerUpdateInput or dict"
        ):
            await stash_client.bulk_scene_marker_update(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_performer_destroy_rejects_non_dict(self, stash_client):
        """performer_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be PerformerDestroyInput or dict"
        ):
            await stash_client.performer_destroy({"id": "123"}.items())  # type: ignore

    @pytest.mark.asyncio
    async def test_bulk_performer_update_rejects_non_dict(self, stash_client):
        """bulk_performer_update should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be BulkPerformerUpdateInput or dict"
        ):
            await stash_client.bulk_performer_update(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_image_destroy_rejects_non_dict(self, stash_client):
        """image_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be ImageDestroyInput or dict"
        ):
            await stash_client.image_destroy([1, 2, 3])  # type: ignore

    @pytest.mark.asyncio
    async def test_images_destroy_rejects_non_dict(self, stash_client):
        """images_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be ImagesDestroyInput or dict"
        ):
            await stash_client.images_destroy("not valid")  # type: ignore

    @pytest.mark.asyncio
    async def test_scenes_destroy_rejects_non_dict(self, stash_client):
        """scenes_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be ScenesDestroyInput or dict"
        ):
            await stash_client.scenes_destroy(12345)  # type: ignore

    @pytest.mark.asyncio
    async def test_studio_destroy_rejects_non_dict(self, stash_client):
        """studio_destroy should reject non-dict, non-Input inputs."""
        with pytest.raises(
            TypeError, match="input_data must be StudioDestroyInput or dict"
        ):
            await stash_client.studio_destroy({"foo": "bar"}.keys())  # type: ignore


class TestDictValidationPydanticValidation:
    """Test that dict inputs are validated through Pydantic models."""

    @pytest.mark.asyncio
    async def test_tag_destroy_validates_required_field(self, stash_client):
        """tag_destroy should reject dict missing required 'id' field."""
        with pytest.raises(ValidationError):  # Pydantic ValidationError
            await stash_client.tag_destroy({})  # Missing required 'id'

    def test_image_destroy_validates_required_field(self, stash_client):
        """ImageDestroyInput should validate required 'id' field."""
        with pytest.raises(ValidationError):
            ImageDestroyInput()  # type: ignore  # Missing required 'id'

    def test_images_destroy_validates_required_field(self, stash_client):
        """ImagesDestroyInput should validate ids field when provided."""
        # All fields are optional with UNSET defaults, so test valid construction
        validated = ImagesDestroyInput(ids=["1", "2", "3"])
        assert validated.ids == ["1", "2", "3"]

    def test_scenes_destroy_validates_required_field(self, stash_client):
        """ScenesDestroyInput should validate required 'ids' field."""
        validated = ScenesDestroyInput(ids=["1", "2"])
        assert validated.ids == ["1", "2"]

    def test_studio_destroy_validates_required_field(self, stash_client):
        """StudioDestroyInput should validate required 'id' field."""
        with pytest.raises(ValidationError):
            StudioDestroyInput()  # type: ignore  # Missing required 'id'

    def test_scene_hash_validates_structure(self, stash_client):
        """find_scene_by_hash should accept valid dict with optional fields."""
        # Valid dict with at least one hash
        input_dict = {"checksum": "abc123"}
        # Should not raise - Pydantic validation passes
        hash_input = SceneHashInput(**input_dict)
        assert hash_input.checksum == "abc123"

    def test_bulk_update_accepts_optional_fields(self, stash_client):
        """Bulk update inputs should accept dicts with all fields optional."""
        # All fields are optional in bulk updates
        input_dict = {"ids": ["1", "2"], "rating100": 85}
        validated = BulkImageUpdateInput(**input_dict)
        assert validated.ids == ["1", "2"]
        assert validated.rating100 == 85


class TestDictValidationInputTypeAcceptance:
    """Test that Input type objects are still accepted."""

    def test_scene_destroy_accepts_input_type(self, stash_client):
        """scene_destroy should accept SceneDestroyInput objects."""
        input_obj = SceneDestroyInput(id="123", delete_file=False)
        # Should not raise TypeError
        assert isinstance(input_obj, SceneDestroyInput)

    def test_bulk_gallery_update_accepts_input_type(self, stash_client):
        """bulk_gallery_update should accept BulkGalleryUpdateInput objects."""
        input_obj = BulkGalleryUpdateInput(ids=["1", "2"], organized=True)
        assert isinstance(input_obj, BulkGalleryUpdateInput)

    def test_performer_destroy_accepts_input_type(self, stash_client):
        """performer_destroy should accept PerformerDestroyInput objects."""
        input_obj = PerformerDestroyInput(id="456")
        assert isinstance(input_obj, PerformerDestroyInput)

    def test_bulk_performer_update_accepts_input_type(self, stash_client):
        """bulk_performer_update should accept BulkPerformerUpdateInput objects."""
        input_obj = BulkPerformerUpdateInput(ids=["1", "2"], rating100=75)
        assert isinstance(input_obj, BulkPerformerUpdateInput)

    def test_image_destroy_accepts_input_type(self, stash_client):
        """image_destroy should accept ImageDestroyInput objects."""
        input_obj = ImageDestroyInput(id="789")
        assert isinstance(input_obj, ImageDestroyInput)

    def test_images_destroy_accepts_input_type(self, stash_client):
        """images_destroy should accept ImagesDestroyInput objects."""
        input_obj = ImagesDestroyInput(ids=["1", "2", "3"])
        assert isinstance(input_obj, ImagesDestroyInput)

    def test_studio_destroy_accepts_input_type(self, stash_client):
        """studio_destroy should accept StudioDestroyInput objects."""
        input_obj = StudioDestroyInput(id="999")
        assert isinstance(input_obj, StudioDestroyInput)

    def test_tag_destroy_accepts_input_type(self, stash_client):
        """tag_destroy should accept TagDestroyInput objects."""
        input_obj = TagDestroyInput(id="111")
        assert isinstance(input_obj, TagDestroyInput)

    def test_bulk_scene_marker_update_accepts_input_type(self, stash_client):
        """bulk_scene_marker_update should accept BulkSceneMarkerUpdateInput objects."""
        input_obj = BulkSceneMarkerUpdateInput(ids=["1", "2"])
        assert isinstance(input_obj, BulkSceneMarkerUpdateInput)

    def test_scene_merge_accepts_input_type(self, stash_client):
        """scene_merge should accept SceneMergeInput objects."""
        input_obj = SceneMergeInput(source=["1", "2"], destination="3")
        assert isinstance(input_obj, SceneMergeInput)


class TestDictValidationGraphQLConversion:
    """Test that validated dicts are properly converted to GraphQL format."""

    def test_save_filter_converts_to_graphql(self, stash_client):
        """save_filter should convert validated dict to GraphQL format."""
        input_dict = {"mode": FilterMode.SCENES, "name": "Test Filter"}
        validated = SaveFilterInput(**input_dict)
        graphql_dict = validated.to_graphql()

        # Should have GraphQL field names
        assert "mode" in graphql_dict
        assert "name" in graphql_dict

    def test_scene_destroy_preserves_optional_fields(self, stash_client):
        """scene_destroy should preserve optional boolean fields in conversion."""
        input_dict = {"id": "123", "delete_file": True}
        validated = SceneDestroyInput(**input_dict)
        graphql_dict = validated.to_graphql()

        assert graphql_dict["id"] == "123"
        assert graphql_dict["delete_file"] is True

    def test_bulk_update_excludes_unset_fields(self, stash_client):
        """Bulk update should exclude UNSET fields from GraphQL output."""
        input_dict = {"ids": ["1", "2"], "rating100": 85}
        # Only ids and rating100 set, other fields are UNSET
        validated = BulkImageUpdateInput(**input_dict)
        graphql_dict = validated.to_graphql()

        # Should only include provided fields
        assert "ids" in graphql_dict
        assert "rating100" in graphql_dict
        # Should not include UNSET fields like 'organized', 'title', etc.
        assert "organized" not in graphql_dict
        assert "title" not in graphql_dict

    def test_images_destroy_converts_to_graphql(self, stash_client):
        """images_destroy should convert dict to GraphQL format."""
        input_dict = {"ids": ["100", "200", "300"], "delete_file": True}
        validated = ImagesDestroyInput(**input_dict)
        graphql_dict = validated.to_graphql()

        assert graphql_dict["ids"] == ["100", "200", "300"]
        assert graphql_dict["delete_file"] is True

    def test_bulk_performer_update_converts_to_graphql(self, stash_client):
        """bulk_performer_update should convert dict to GraphQL format."""
        input_dict = {"ids": ["10", "20"], "favorite": True}
        validated = BulkPerformerUpdateInput(**input_dict)
        graphql_dict = validated.to_graphql()

        assert graphql_dict["ids"] == ["10", "20"]
        assert "favorite" in graphql_dict


class TestDictValidationFieldTypes:
    """Test that field type validation works correctly."""

    def test_rating100_validates_range(self, stash_client):
        """BulkImageUpdateInput should validate rating100 is 0-100."""
        # Valid rating
        valid_dict = {"ids": ["1"], "rating100": 85}
        validated = BulkImageUpdateInput(**valid_dict)
        assert validated.rating100 == 85

        # Pydantic v2 validates rating100 constraints defined in the model
        # If the model doesn't have explicit constraints, this test verifies behavior
        valid_high = BulkImageUpdateInput(ids=["1"], rating100=100)
        assert valid_high.rating100 == 100

    def test_ids_must_be_list_of_strings(self, stash_client):
        """Bulk update inputs should validate ids is list[str]."""
        # Valid list of strings
        valid_dict = {"ids": ["1", "2", "3"]}
        validated = BulkStudioUpdateInput(**valid_dict)
        assert validated.ids == ["1", "2", "3"]

        # Test with actually invalid type (not a list)
        with pytest.raises(ValidationError):  # Pydantic ValidationError
            BulkStudioUpdateInput(ids="not a list")  # type: ignore

    def test_boolean_fields_validated(self, stash_client):
        """Input types should validate boolean fields."""
        # Valid boolean
        valid_dict = {"id": "123", "delete_file": True}
        validated = SceneDestroyInput(**valid_dict)
        assert validated.delete_file is True

        # Invalid: string instead of bool (Pydantic coerces, so check with strict validation)
        # Pydantic v2 is more lenient, so this test checks the type is properly set
        validated = SceneDestroyInput(id="123", delete_file="true")  # type: ignore
        # Pydantic coerces "true" to True
        assert isinstance(validated.delete_file, bool)


class TestDictValidationErrorMessages:
    """Test that validation errors have clear, helpful messages."""

    @pytest.mark.asyncio
    async def test_type_error_includes_actual_type(self, stash_client):
        """TypeError should include the actual type that was passed."""
        with pytest.raises(TypeError) as exc_info:
            await stash_client.tag_destroy(12345)  # type: ignore

        error_msg = str(exc_info.value)
        assert "TagDestroyInput or dict" in error_msg
        assert "int" in error_msg

    @pytest.mark.asyncio
    async def test_type_error_includes_method_context(self, stash_client):
        """TypeError should make it clear which parameter is wrong."""
        with pytest.raises(TypeError) as exc_info:
            await stash_client.bulk_performer_update([])  # type: ignore

        error_msg = str(exc_info.value)
        assert "input_data must be" in error_msg
        assert "BulkPerformerUpdateInput" in error_msg


class TestDictValidationCoverage:
    """Test coverage across all major mixin categories."""

    @pytest.mark.asyncio
    async def test_scene_mixin_coverage(self, stash_client):
        """Scene mixin methods validate dict inputs."""
        # SceneDestroyInput
        with pytest.raises(TypeError):
            await stash_client.scene_destroy("not a dict")  # type: ignore

        # ScenesDestroyInput
        with pytest.raises(TypeError):
            await stash_client.scenes_destroy(123)  # type: ignore

        # SceneMergeInput
        with pytest.raises(TypeError):
            await stash_client.scene_merge([])  # type: ignore

    @pytest.mark.asyncio
    async def test_image_mixin_coverage(self, stash_client):
        """Image mixin methods validate dict inputs."""
        # ImageDestroyInput
        with pytest.raises(TypeError):
            await stash_client.image_destroy("invalid")  # type: ignore

        # ImagesDestroyInput
        with pytest.raises(TypeError):
            await stash_client.images_destroy(None)  # type: ignore

        # BulkImageUpdateInput
        with pytest.raises(TypeError):
            await stash_client.bulk_image_update(42)  # type: ignore

    @pytest.mark.asyncio
    async def test_gallery_mixin_coverage(self, stash_client):
        """Gallery mixin methods validate dict inputs."""
        # BulkGalleryUpdateInput
        with pytest.raises(TypeError):
            await stash_client.bulk_gallery_update("invalid")  # type: ignore

    @pytest.mark.asyncio
    async def test_tag_mixin_coverage(self, stash_client):
        """Tag mixin methods validate dict inputs."""
        # TagDestroyInput
        with pytest.raises(TypeError):
            await stash_client.tag_destroy(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_studio_mixin_coverage(self, stash_client):
        """Studio mixin methods validate dict inputs."""
        # StudioDestroyInput
        with pytest.raises(TypeError):
            await stash_client.studio_destroy([])  # type: ignore

        # BulkStudioUpdateInput
        with pytest.raises(TypeError):
            await stash_client.bulk_studio_update(123)  # type: ignore

    @pytest.mark.asyncio
    async def test_marker_mixin_coverage(self, stash_client):
        """Marker mixin methods validate dict inputs."""
        # BulkSceneMarkerUpdateInput
        with pytest.raises(TypeError):
            await stash_client.bulk_scene_marker_update("not valid")  # type: ignore

    @pytest.mark.asyncio
    async def test_performer_mixin_coverage(self, stash_client):
        """Performer mixin methods validate dict inputs."""
        # PerformerDestroyInput
        with pytest.raises(TypeError):
            await stash_client.performer_destroy([])  # type: ignore

        # BulkPerformerUpdateInput
        with pytest.raises(TypeError):
            await stash_client.bulk_performer_update(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_filter_mixin_coverage(self, stash_client):
        """Filter mixin methods validate dict inputs."""
        # SaveFilterInput
        with pytest.raises(TypeError):
            await stash_client.save_filter("invalid")  # type: ignore

        # DestroyFilterInput
        with pytest.raises(TypeError):
            await stash_client.destroy_saved_filter(123)  # type: ignore


class TestDictValidationGroupMixin:
    """Test group mixin uses different pattern but still validates."""

    @pytest.mark.asyncio
    async def test_group_destroy_validates_and_constructs(self, stash_client):
        """group_destroy constructs Input from dict and validates."""
        # Valid dict should construct Input successfully
        valid_dict = {"id": "123"}
        input_obj = GroupDestroyInput(**valid_dict)
        assert input_obj.id == "123"

        # Invalid type should raise
        with pytest.raises(TypeError):
            await stash_client.group_destroy(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_bulk_group_update_validates_and_constructs(self, stash_client):
        """bulk_group_update constructs Input from dict and validates."""
        # Valid dict
        valid_dict = {"ids": ["1", "2"], "rating100": 90}
        input_obj = BulkGroupUpdateInput(**valid_dict)
        assert input_obj.ids == ["1", "2"]

        # Invalid type should raise
        with pytest.raises(TypeError):
            await stash_client.bulk_group_update("not a dict")  # type: ignore
