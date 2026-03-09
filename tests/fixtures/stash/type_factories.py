"""FactoryBoy factories for Stash API types.

This module provides factories for creating test instances of Stash API types
(Performer, Studio, Scene, etc.) using FactoryBoy. These are NOT SQLAlchemy models,
but rather Strawberry GraphQL types used to interact with the Stash API.

Usage:
    from tests.fixtures import PerformerFactory, StudioFactory

    # Create a test performer
    performer = PerformerFactory(name="Test Performer")

    # Create a performer with specific attributes
    performer = PerformerFactory(
        id="123",
        name="Jane Doe",
        gender=GenderEnum.FEMALE,
    )
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from factory.base import Factory
from factory.declarations import LazyFunction, Sequence

from stash_graphql_client.types import (
    Gallery,
    Group,
    Image,
    Performer,
    Scene,
    Studio,
    Tag,
)
from stash_graphql_client.types.files import Fingerprint, ImageFile, VideoFile
from stash_graphql_client.types.job import Job, JobStatus
from stash_graphql_client.types.scene import SceneCreateInput
from stash_graphql_client.types.unset import UNSET


class PerformerFactory(Factory):
    """Factory for Performer Stash API type.

    Creates Performer instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic performer
        performer = PerformerFactory()

        # Create a performer with specific values
        performer = PerformerFactory(
            id="123",
            name="Jane Doe",
            gender=GenderEnum.FEMALE,
            urls=["https://example.com/performer"]
        )
    """

    class Meta:
        model = Performer

    # Required fields
    id = Sequence(lambda n: str(100 + n))
    __typename = "Performer"
    name = Sequence(lambda n: f"Performer_{n}")

    # Lists with default factories
    # All lists are non-nullable [Type!]! in GraphQL, use []
    alias_list = LazyFunction(list)
    tags = LazyFunction(list)
    stash_ids = LazyFunction(list)
    scenes = LazyFunction(list)
    groups = LazyFunction(list)
    urls = LazyFunction(list)

    # Optional fields
    disambiguation = None
    gender = None
    birthdate = None
    ethnicity = None
    country = None
    eye_color = None
    height_cm = None
    measurements = None
    fake_tits = None
    penis_length = None
    circumcised = None
    career_length = None
    tattoos = None
    piercings = None
    image_path = None
    details = None
    death_date = None
    hair_color = None
    weight = None


class StudioFactory(Factory):
    """Factory for Studio Stash API type.

    Creates Studio instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic studio
        studio = StudioFactory()

        # Create a studio with specific values
        studio = StudioFactory(
            id="456",
            name="Test Studio",
            urls=["https://example.com/studio"]
        )
    """

    class Meta:
        model = Studio

    # Required fields
    id = Sequence(lambda n: str(200 + n))
    __typename = "Studio"
    name = Sequence(lambda n: f"Studio_{n}")

    # Studio list fields are all nullable in GraphQL, so use None
    urls = None
    aliases = None
    tags = None
    stash_ids = None
    parent_studio = None
    details = None
    image_path = None


class TagFactory(Factory):
    """Factory for Tag Stash API type.

    Creates Tag instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic tag
        tag = TagFactory()

        # Create a tag with specific values
        tag = TagFactory(
            id="789",
            name="Test Tag",
            description="A test tag description"
        )
    """

    class Meta:
        model = Tag

    # Required fields
    id = Sequence(lambda n: str(300 + n))
    __typename = "Tag"
    name = Sequence(lambda n: f"Tag_{n}")

    # Tag list fields are all nullable in GraphQL, so use None
    aliases = None
    parents = None
    children = None

    # Optional fields
    description = None
    image_path = None


class SceneFactory(Factory):
    """Factory for Scene Stash API type.

    Creates Scene instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic scene
        scene = SceneFactory()

        # Create a scene with specific values
        scene = SceneFactory(
            id="1001",
            title="Test Scene",
            studio=StudioFactory()
        )
    """

    class Meta:
        model = Scene

    # Required fields
    id = Sequence(lambda n: str(400 + n))
    __typename = "Scene"
    title = Sequence(lambda n: f"Scene_{n}")

    # Lists with default factories
    # Most Scene lists are non-nullable [Type!]! in GraphQL, use []
    files = LazyFunction(list)
    tags = LazyFunction(list)
    performers = LazyFunction(list)
    stash_ids = LazyFunction(list)
    groups = LazyFunction(list)
    urls = LazyFunction(list)
    galleries = LazyFunction(list)
    scene_markers = LazyFunction(list)
    sceneStreams = LazyFunction(list)
    # captions is nullable [VideoCaption!] in GraphQL, use None
    captions = None

    # Optional fields
    code = None
    details = None
    director = None
    date = None
    rating100 = None
    o_counter = None
    organized = False
    studio = None
    # paths is an object field (ScenePathsType | UnsetType), use UNSET not None
    paths = UNSET


class GalleryFactory(Factory):
    """Factory for Gallery Stash API type.

    Creates Gallery instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic gallery
        gallery = GalleryFactory()

        # Create a gallery with specific values
        gallery = GalleryFactory(
            id="2001",
            title="Test Gallery",
            image_count=50
        )
    """

    class Meta:
        model = Gallery

    # Required fields
    id = Sequence(lambda n: str(500 + n))
    __typename = "Gallery"
    title = Sequence(lambda n: f"Gallery_{n}")

    # Lists with default factories
    files = LazyFunction(list)
    tags = LazyFunction(list)
    performers = LazyFunction(list)
    scenes = LazyFunction(list)
    urls = LazyFunction(list)
    chapters = LazyFunction(list)

    # Optional fields
    code = None
    date = None
    details = None
    photographer = None
    rating100 = None
    organized = False
    studio = None
    image_count = 0
    folder = None


class ImageFactory(Factory):
    """Factory for Image Stash API type.

    Creates Image instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic image
        image = ImageFactory()

        # Create an image with specific values
        image = ImageFactory(
            id="3001",
            title="Test Image",
            organized=True
        )
    """

    class Meta:
        model = Image

    # Required fields
    id = Sequence(lambda n: str(600 + n))
    __typename = "Image"
    title = Sequence(lambda n: f"Image_{n}")

    # Lists with default factories
    visual_files = LazyFunction(list)
    tags = LazyFunction(list)
    performers = LazyFunction(list)
    galleries = LazyFunction(list)
    urls = LazyFunction(list)

    # Optional fields
    code = None
    date = None
    details = None
    photographer = None
    organized = False
    studio = None
    # paths is an object field (ImagePathsType | UnsetType), use UNSET not None
    paths = UNSET


class GroupFactory(Factory):
    """Factory for Group Stash API type.

    Creates Group instances with realistic defaults for testing Stash API
    interactions without needing a real Stash server.

    Example:
        # Create a basic group
        group = GroupFactory()

        # Create a group with specific values
        group = GroupFactory(
            id="4001",
            name="Test Series",
            duration=7200
        )
    """

    class Meta:
        model = Group

    # Required fields
    id = Sequence(lambda n: str(700 + n))
    __typename = "Group"
    name = Sequence(lambda n: f"Group_{n}")

    # Lists with default factories
    tags = LazyFunction(list)
    scenes = LazyFunction(list)
    urls = LazyFunction(list)
    containing_groups = LazyFunction(list)
    sub_groups = LazyFunction(list)

    # Optional fields
    aliases = None
    duration = None
    date = None
    studio = None
    director = None
    synopsis = None
    front_image_path = None
    back_image_path = None


class ImageFileFactory(Factory):
    """Factory for ImageFile Stash API type.

    Creates ImageFile instances representing image files in Stash, with realistic
    defaults for testing file operations without needing a real Stash server.

    Based on GraphQL schema: schema/types/file.graphql (ImageFile type)

    Example:
        # Create a basic image file
        image_file = ImageFileFactory()

        # Create an image file with specific values
        image_file = ImageFileFactory(
            id="8001",
            path="/path/to/image.jpg",
            basename="image.jpg",
            width=1920,
            height=1080
        )
    """

    class Meta:
        model = ImageFile

    # Required fields from BaseFile (inherited via StashObject)
    id = Sequence(lambda n: str(800 + n))
    __typename = "ImageFile"
    path = Sequence(lambda n: f"/test/images/image_{n}.jpg")
    basename = Sequence(lambda n: f"image_{n}.jpg")
    mod_time = LazyFunction(lambda: datetime.now(UTC))
    size = 1024000  # 1 MB default

    # Required fields - fingerprints list
    fingerprints = LazyFunction(list[Fingerprint])

    # ImageFile specific required fields
    width = 1920
    height = 1080


class VideoFileFactory(Factory):
    """Factory for VideoFile Stash API type.

    Creates VideoFile instances representing video files in Stash, with realistic
    defaults for testing file operations without needing a real Stash server.

    Based on GraphQL schema: schema/types/file.graphql (VideoFile type)

    Example:
        # Create a basic video file
        video_file = VideoFileFactory()

        # Create a video file with specific values
        video_file = VideoFileFactory(
            id="9001",
            path="/path/to/video.mp4",
            basename="video.mp4",
            duration=3600.0,
            video_codec="h264"
        )
    """

    class Meta:
        model = VideoFile

    # Required fields from BaseFile (inherited via StashObject)
    id = Sequence(lambda n: str(900 + n))
    __typename = "VideoFile"
    path = Sequence(lambda n: f"/test/videos/video_{n}.mp4")
    basename = Sequence(lambda n: f"video_{n}.mp4")
    mod_time = LazyFunction(lambda: datetime.now(UTC))
    size = 10240000  # 10 MB default

    # Required fields - fingerprints list
    fingerprints = LazyFunction(list[Fingerprint])

    # VideoFile specific required fields
    format = "mp4"
    width = 1920
    height = 1080
    duration = 60.0  # 60 seconds
    video_codec = "h264"
    audio_codec = "aac"
    frame_rate = 30.0
    bit_rate = 5000000  # 5 Mbps


class JobFactory(Factory):
    """Factory for Job Stash API type.

    Creates Job instances representing Stash background jobs, with realistic
    defaults for testing job operations without needing a real Stash server.

    Based on GraphQL schema: schema/types/job.graphql (Job type)

    Example:
        # Create a finished job
        job = JobFactory(status=JobStatus.FINISHED)

        # Create a running job with progress
        job = JobFactory(
            id="job_123",
            status=JobStatus.RUNNING,
            progress=50.0,
            description="Scanning metadata"
        )
    """

    class Meta:
        model = Job

    # Required fields
    id = Sequence(lambda n: f"job_{n}")
    __typename = "Job"
    status = JobStatus.FINISHED
    subTasks = LazyFunction(list)
    description = Sequence(lambda n: f"Job_{n}")
    addTime = LazyFunction(lambda: datetime.now(UTC))

    # Optional fields
    progress = None
    startTime = None
    endTime = None
    error = None


# ============================================================================
# Pytest Fixtures for Stash API Types
# ============================================================================


@pytest.fixture
def mock_performer():
    """Fixture for Performer test instance.

    Returns a real Performer object (not a mock) using PerformerFactory.
    All Performer methods work as expected.

    Example:
        def test_something(mock_performer):
            assert mock_performer.name == "Performer_0"
            assert mock_performer.id == "100"
    """
    return PerformerFactory(id="123", name="test_user")


@pytest.fixture
def mock_studio():
    """Fixture for Studio test instance.

    Returns a real Studio object (not a mock) using StudioFactory.

    Example:
        def test_something(mock_studio):
            assert mock_studio.name == "Test Studio"
            assert mock_studio.id == "123"
    """
    return StudioFactory(id="123", name="Test Studio")


@pytest.fixture
def mock_tag():
    """Fixture for Tag test instance.

    Returns a real Tag object (not a mock) using TagFactory.

    Example:
        def test_something(mock_tag):
            assert mock_tag.name == "test_tag"
            assert mock_tag.id == "123"
    """
    return TagFactory(id="123", name="test_tag")


@pytest.fixture
def mock_scene():
    """Fixture for Scene test instance.

    Returns a real Scene object (not a mock) using SceneFactory.

    Example:
        def test_something(mock_scene):
            assert mock_scene.title == "Test Scene"
            assert mock_scene.id == "123"
    """
    return SceneFactory(id="123", title="Test Scene")


@pytest.fixture
def mock_gallery():
    """Fixture for Gallery test instance.

    Returns a real Gallery object (not a mock) using GalleryFactory.

    Example:
        def test_something(mock_gallery):
            assert mock_gallery.title == "Test Gallery"
            assert mock_gallery.id == "123"
    """
    return GalleryFactory(
        id="123",
        title="Test Gallery",
        code="12345",
        organized=True,
    )


@pytest.fixture
def mock_image():
    """Fixture for Image test instance.

    Returns a real Image object (not a mock) using ImageFactory.

    Example:
        def test_something(mock_image):
            assert mock_image.title == "Test Image"
            assert mock_image.id == "123"
    """
    return ImageFactory(
        id="123",
        title="Test Image",
        organized=False,
    )


@pytest.fixture
def mock_image_file():
    """Fixture for ImageFile test instance.

    Returns a real ImageFile object (not a mock) using ImageFileFactory.

    Example:
        def test_something(mock_image_file):
            assert mock_image_file.path == "/path/to/image.jpg"
            assert mock_image_file.width == 1920
    """
    return ImageFileFactory(
        id="123",
        path="/path/to/image.jpg",
        basename="image.jpg",
        size=12345,
        width=1920,
        height=1080,
    )


@pytest.fixture
def mock_video_file():
    """Fixture for VideoFile test instance.

    Returns a real VideoFile object (not a mock) using VideoFileFactory.

    Example:
        def test_something(mock_video_file):
            assert mock_video_file.path == "/path/to/video.mp4"
            assert mock_video_file.duration == 60.0
    """
    return VideoFileFactory(
        id="456",
        path="/path/to/video.mp4",
        basename="video.mp4",
        size=123456,
        duration=60.0,
        video_codec="h264",
        audio_codec="aac",
        width=1920,
        height=1080,
    )


@pytest.fixture
def enable_scene_creation():
    """Enable scene creation during tests using patch.object context manager.

    This fixture temporarily sets Scene.__create_input_type__ to SceneCreateInput,
    allowing scenes to be created directly during testing. It uses patch.object
    for cleaner setup/teardown handling compared to manual attribute manipulation.

    Without this fixture, Scene objects normally cannot be created directly via API
    because the __create_input_type__ attribute is not set by default.

    The fixture uses patch.object which automatically handles:
    - Storing the original value (if any)
    - Setting the new value for the duration of the test
    - Restoring the original value after the test completes
    - Proper cleanup even if the test raises an exception

    Yields:
        None: This fixture doesn't provide a value, it just modifies Scene class state

    Example:
        ```python
        @pytest.mark.asyncio
        async def test_scene_creation(stash_client, enable_scene_creation):
            # With this fixture, Scene objects can be created directly
            scene = Scene(
                title="Test Scene",
                urls=["https://example.com/scene"],
                organized=True,
            )
            scene = await stash_client.create_scene(scene)
            assert scene.id is not None
        ```

        ```python
        @pytest.mark.asyncio
        async def test_save_with_scene(respx_stash_client, enable_scene_creation):
            # Can also be used with store.save()
            import uuid
            from stash_graphql_client import StashEntityStore
            scene = Scene(id=uuid.uuid4().hex, title="New Scene")
            scene._is_new = True

            # Mock the GraphQL response
            respx.post("http://localhost:9999/graphql").mock(
                return_value=httpx.Response(200, json={
                    "data": {"sceneCreate": {"id": "123", "title": "New Scene"}}
                })
            )

            store = StashEntityStore(respx_stash_client)
            await store.save(scene)
            assert scene.id == "123"
        ```
    """
    with patch.object(Scene, "__create_input_type__", SceneCreateInput):
        yield


# Export all factories and fixtures
__all__ = [
    # Factories
    "GalleryFactory",
    "GroupFactory",
    "ImageFactory",
    "ImageFileFactory",
    "JobFactory",
    "PerformerFactory",
    "SceneFactory",
    "StudioFactory",
    "TagFactory",
    "VideoFileFactory",
    "mock_gallery",
    "mock_image",
    "mock_image_file",
    # Pytest fixtures
    "mock_performer",
    "mock_scene",
    "mock_studio",
    "mock_tag",
    "mock_video_file",
    "enable_scene_creation",
]
