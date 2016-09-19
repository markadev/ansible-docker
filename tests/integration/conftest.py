from __future__ import absolute_import, print_function, unicode_literals
import docker
import pkg_resources
import pytest


@pytest.fixture
def basic_config():
    return pkg_resources.resource_filename(__name__, 'basic.yml')


@pytest.fixture
def docker_client():
    return docker.Client()


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
            self.docker_client.remove_image(resource_id=img_id)


@pytest.fixture
def image_tracker(docker_client):
    tracker = ImageTracker(docker_client)
    yield tracker
    tracker.remove_images()


# vim:set ts=4 sw=4 expandtab:
