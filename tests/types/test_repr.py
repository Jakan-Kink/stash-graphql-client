"""Tests for StashObject shallow __repr__ and _short_repr()."""

from __future__ import annotations

from typing import ClassVar

from stash_graphql_client.types.base import StashObject
from stash_graphql_client.types.performer import Performer
from stash_graphql_client.types.scene import Scene
from stash_graphql_client.types.studio import Studio
from stash_graphql_client.types.tag import Tag


class TestShortRepr:
    """Tests for _short_repr() — compact representation for nested display."""

    def test_short_repr_uses_label_field(self):
        """Short repr shows the label field (e.g. name for Tag)."""
        tag = Tag(id="1", name="blonde")
        assert tag._short_repr() == "Tag(name='blonde')"

    def test_short_repr_falls_back_to_id(self):
        """When label field is UNSET, falls back to id."""
        tag = Tag(id="42")
        assert tag._short_repr() == "Tag(id='42')"

    def test_short_repr_falls_back_when_label_is_none(self):
        """When label field is explicitly None, falls back to id."""
        tag = Tag(id="42", name=None)
        assert tag._short_repr() == "Tag(id='42')"

    def test_short_repr_scene_title(self):
        """Scene uses title for short repr."""
        scene = Scene(id="s1", title="My Movie")
        assert scene._short_repr() == "Scene(title='My Movie')"

    def test_short_repr_performer_name(self):
        """Performer uses name for short repr."""
        perf = Performer(id="p1", name="Jane Doe")
        assert perf._short_repr() == "Performer(name='Jane Doe')"

    def test_short_repr_studio_name(self):
        """Studio uses name for short repr."""
        studio = Studio(id="st1", name="Acme Studios")
        assert studio._short_repr() == "Studio(name='Acme Studios')"

    def test_short_repr_multiple_fields(self):
        """Short repr collects all set fields from the tuple."""

        class Multi(StashObject):
            __type_name__ = "Multi"
            __short_repr_fields__ = ("id", "name")
            __update_input_type__ = None  # type: ignore[assignment]
            __tracked_fields__: ClassVar[set[str]] = set()
            name: str | None = None

        obj = Multi(id="42", name="Alice")
        assert obj._short_repr() == "Multi(id='42', name='Alice')"

    def test_short_repr_multiple_fields_partial(self):
        """Short repr skips UNSET/None fields in multi-field tuple."""

        class Multi(StashObject):
            __type_name__ = "Multi"
            __short_repr_fields__ = ("id", "name", "label")
            __update_input_type__ = None  # type: ignore[assignment]
            __tracked_fields__: ClassVar[set[str]] = set()
            name: str | None = None
            label: str | None = None

        obj = Multi(id="42", name=None, label="x")
        # id is set, name is None (skipped), label is set
        assert obj._short_repr() == "Multi(id='42', label='x')"

    def test_short_repr_no_short_repr_fields(self):
        """Base StashObject with no __short_repr_fields__ always uses id."""

        class Bare(StashObject):
            __type_name__ = "Bare"
            __update_input_type__ = None  # type: ignore[assignment]
            __tracked_fields__: ClassVar[set[str]] = set()

        obj = Bare(id="xyz")
        assert obj._short_repr() == "Bare(id='xyz')"


class TestRepr:
    """Tests for __repr__ — full representation with shallow relationships."""

    def test_basic_repr_shows_id_and_set_fields(self):
        """Repr shows id and all non-UNSET fields."""
        tag = Tag(id="1", name="test", description="A tag")
        r = repr(tag)
        assert r.startswith("Tag(")
        assert "id='1'" in r
        assert "name='test'" in r
        assert "description='A tag'" in r

    def test_unset_fields_omitted(self):
        """UNSET fields are not shown in repr."""
        tag = Tag(id="1", name="test")
        r = repr(tag)
        assert "description=" not in r
        assert "aliases=" not in r

    def test_single_relationship_uses_short_repr(self):
        """A single StashObject relationship renders via _short_repr()."""
        studio = Studio(id="st1", name="Acme")
        scene = Scene(id="s1", title="Movie", studio=studio)
        r = repr(scene)
        assert "studio=Studio(name='Acme')" in r

    def test_list_relationship_shows_first_two(self):
        """List of StashObjects shows first 2 items then ..N more."""
        tags = [Tag(id=str(i), name=f"tag{i}") for i in range(5)]
        scene = Scene(id="s1", tags=tags)
        r = repr(scene)
        assert "tags=[Tag(name='tag0'), Tag(name='tag1'), ..3 more]" in r

    def test_list_relationship_two_items_no_truncation(self):
        """List with exactly 2 items shows all, no truncation suffix."""
        tags = [Tag(id="1", name="a"), Tag(id="2", name="b")]
        scene = Scene(id="s1", tags=tags)
        r = repr(scene)
        assert "tags=[Tag(name='a'), Tag(name='b')]" in r
        assert "more" not in r.split("tags=")[1].split("]")[0]

    def test_list_relationship_one_item(self):
        """List with 1 item shows it without truncation."""
        tags = [Tag(id="1", name="solo")]
        scene = Scene(id="s1", tags=tags)
        r = repr(scene)
        assert "tags=[Tag(name='solo')]" in r

    def test_empty_list_shown(self):
        """Empty list is shown as []."""
        scene = Scene(id="s1", tags=[])
        r = repr(scene)
        assert "tags=[]" in r

    def test_long_scalar_truncated(self):
        """Scalar repr longer than 200 chars is truncated."""
        long_text = "x" * 300
        tag = Tag(id="1", description=long_text)
        r = repr(tag)
        # The description repr should be truncated
        desc_part = r.split("description=")[1].split(", ")[0].rstrip(")")
        assert len(desc_part) <= 200

    def test_field_order_is_sorted(self):
        """Fields appear in sorted order for determinism."""
        tag = Tag(id="1", name="test", aliases=["a"], description="desc")
        r = repr(tag)
        # Extract field positions
        aliases_pos = r.index("aliases=")
        desc_pos = r.index("description=")
        name_pos = r.index("name=")
        # id is always first, then alphabetical
        assert aliases_pos < desc_pos < name_pos

    def test_id_always_first(self):
        """id= always appears as the first field."""
        tag = Tag(id="1", name="test", aliases=["a"])
        r = repr(tag)
        # id should be the first field after the opening paren
        after_paren = r.split("(", 1)[1]
        assert after_paren.startswith("id=")

    def test_none_value_shown(self):
        """Explicitly set None values are shown (they're not UNSET)."""
        tag = Tag(id="1", name=None)
        r = repr(tag)
        assert "name=None" in r

    def test_subclass_short_repr_fields_override(self):
        """Subclasses can customize __short_repr_fields__."""

        class CustomEntity(StashObject):
            __type_name__ = "Custom"
            __short_repr_fields__ = ("label",)
            __update_input_type__ = None  # type: ignore[assignment]
            __tracked_fields__: ClassVar[set[str]] = set()
            label: str | None = None

        entity = CustomEntity(id="1", label="my-label")
        assert entity._short_repr() == "Custom(label='my-label')"

    def test_repr_with_bool_field(self):
        """Boolean fields render correctly."""
        perf = Performer(id="1", name="Test", favorite=True)
        r = repr(perf)
        assert "favorite=True" in r

    def test_repr_with_int_field(self):
        """Integer fields render correctly."""
        tag = Tag(id="1", scene_count=42)
        r = repr(tag)
        assert "scene_count=42" in r

    def test_repr_does_not_recurse_bidirectional(self):
        """Repr of objects with bidirectional refs doesn't infinitely recurse.

        This is the core problem this feature solves: Scene→Performer→Scene
        should not expand each nested object recursively.
        """
        perf = Performer(id="p1", name="Jane")
        scene = Scene(id="s1", title="Movie", performers=[perf])
        # Manually set up bidirectional reference
        perf.scenes = [scene]

        # These should complete quickly without recursion
        scene_repr = repr(scene)
        perf_repr = repr(perf)

        # Scene's repr shows performer via _short_repr (no expansion)
        assert "Performer(name='Jane')" in scene_repr
        # Performer's repr shows scene via _short_repr (no expansion)
        assert "Scene(title='Movie')" in perf_repr


class TestReprFileTypes:
    """Tests for file type repr."""

    def test_video_file_short_repr(self):
        """VideoFile inherits basename for short repr from BaseFile."""
        from stash_graphql_client.types.files import VideoFile

        vf = VideoFile(id="f1", basename="clip.mp4")
        assert vf._short_repr() == "VideoFile(basename='clip.mp4')"

    def test_folder_short_repr(self):
        """Folder uses path for short repr."""
        from stash_graphql_client.types.files import Folder

        folder = Folder(id="d1", path="/media/videos")
        assert folder._short_repr() == "Folder(path='/media/videos')"
