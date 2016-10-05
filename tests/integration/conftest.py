from __future__ import absolute_import, print_function, unicode_literals
import docker
import pkg_resources
import pytest


@pytest.fixture
def basic_config():
    return pkg_resources.resource_filename(__name__, 'basic.yml')


@pytest.fixture
def failing_config():
    return pkg_resources.resource_filename(__name__, 'failing.yml')


@pytest.fixture
def complex_config():
    return pkg_resources.resource_filename(__name__, 'complex.yml')


@pytest.fixture(scope='session')
def docker_client():
    return docker.from_env()


@pytest.fixture(scope='session')
def base_image(docker_client):
    """Pulls the base image used for building all the test images."""
    docker_client.pull('python', tag='2.7-slim')


class ImageTracker(object):
    def __init__(self, docker_client):
        self.docker_client = docker_client
        self.initial_imageset = set(self._image_id_list())

    def _image_id_list(self):
        return [img['Id'] for img in self.docker_client.images()]

    def get_image_ids(self):
        """Returns a list of new images created since test start"""
        current_imageset = set(self._image_id_list())
        return list(current_imageset - self.initial_imageset)

    def remove_images(self):
        """Removes all the images created since test start"""
        for img_id in self.get_image_ids():
            # Get and remove all tags for the image first
            img_info = self.docker_client.inspect_image(resource_id=img_id)
            repotags = img_info.get('RepoTags', [])
            if repotags is None:
                repotags = []
            for repotag in repotags:
                self.docker_client.remove_image(resource_id=repotag)

            # If there were no tags then remove by the image ID
            if len(repotags) == 0:
                self.docker_client.remove_image(resource_id=img_id)


@pytest.fixture
def image_tracker(base_image, docker_client):
    tracker = ImageTracker(docker_client)
    yield tracker
    tracker.remove_images()


# vim:set ts=4 sw=4 expandtab:
