"""Inverse-relationship sync for file reverse relationships (stashapp/stash #6938).

Setting a file's reverse list (``VideoFile.scenes`` / ``ImageFile.images`` /
``GalleryFile.galleries``) must back-reference the owning entity's file list,
and vice versa, via ``_sync_inverse_relationship`` / ``_add_to_inverse``.

The ``Image.visual_files`` field is a ``VideoFile | ImageFile`` union whose
inverse is ``Image.images`` — but only ``ImageFile`` carries an ``images``
back-ref, so ``VideoFile`` members (e.g. animated images) must be skipped
gracefully rather than crash. These are pure type-layer behaviors (no HTTP).
"""

import pytest

from stash_graphql_client import Gallery, Image, Scene
from stash_graphql_client.types.files import GalleryFile, ImageFile, VideoFile


class TestFileReverseInverseSync:
    """Setting a file's reverse list back-references the entity's file list."""

    @pytest.mark.unit
    def test_video_file_scenes_back_references_scene_files(self) -> None:
        """VideoFile.scenes = [scene] -> scene.files includes the VideoFile."""
        video_file = VideoFile(id="990001", path="/v.mp4")
        scene = Scene(id="990002", title="S1")

        video_file.scenes = [scene]

        assert isinstance(scene.files, list)
        assert video_file in scene.files

    @pytest.mark.unit
    def test_image_file_images_back_references_image_visual_files(self) -> None:
        """ImageFile.images = [image] -> image.visual_files includes the ImageFile."""
        image_file = ImageFile(id="990003", path="/i.jpg")
        image = Image(id="990004", title="I1")

        image_file.images = [image]

        assert isinstance(image.visual_files, list)
        assert image_file in image.visual_files

    @pytest.mark.unit
    def test_gallery_file_galleries_back_references_gallery_files(self) -> None:
        """GalleryFile.galleries = [gallery] -> gallery.files includes the file."""
        gallery_file = GalleryFile(id="990005", path="/g.zip")
        gallery = Gallery(id="990006", title="G1")

        gallery_file.galleries = [gallery]

        assert isinstance(gallery.files, list)
        assert gallery_file in gallery.files


class TestVisualFilesUnionInverseSync:
    """Image.visual_files is a VideoFile|ImageFile union; only ImageFile has the
    inverse ``images`` back-ref."""

    @pytest.mark.unit
    def test_visual_files_syncs_image_file_and_skips_video_file(self) -> None:
        """Setting visual_files to a mixed union back-references the ImageFile
        member and skips the VideoFile member without error."""
        image = Image(id="990007", title="I2")
        image_file = ImageFile(id="990008", path="/i2.jpg")
        video_file = VideoFile(id="990009", path="/anim.gif")

        # No crash despite the VideoFile member lacking an 'images' relationship.
        image.visual_files = [image_file, video_file]

        # ImageFile member got the back-ref...
        assert isinstance(image_file.images, list)
        assert image in image_file.images
        # ...and the VideoFile member was skipped (it has no 'images' field).
        assert not hasattr(video_file, "images")
        assert "images" not in video_file.__relationships__
