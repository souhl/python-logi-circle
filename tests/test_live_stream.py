"""The tests for the Logi API platform."""
import json
import os
from unittest.mock import MagicMock
import aresponses
from tests.test_base import LogiUnitTestBase
from logi_circle.camera import Camera
from logi_circle.const import (API_HOST,
                               ACCESSORIES_ENDPOINT,
                               RTSP_ENDPOINT,
                               LIVE_IMAGE_ENDPOINT,
                               ACCEPT_IMAGE_HEADER,
                               DEFAULT_IMAGE_QUALITY,
                               DEFAULT_IMAGE_REFRESH)
from .helpers import async_return, FakeStream
TEMP_IMAGE = 'temp.jpg'


class TestCamera(LogiUnitTestBase):
    """Unit test for the Camera class."""

    def cleanup(self):
        """Cleanup any data created from the tests."""
        if os.path.isfile(TEMP_IMAGE):
            os.remove(TEMP_IMAGE)

    def test_get_image(self):
        """Test response handling for get_image method"""
        gen1_fixture = json.loads(self.fixtures['accessories'])[0]
        test_camera = Camera(self.logi, gen1_fixture)
        self.logi.auth_provider = self.get_authorized_auth_provider()
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, test_camera.id, LIVE_IMAGE_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'get',
                          aresponses.Response(status=200,
                                              text="Look ma I'm an image",
                                              headers={'content-type': 'image/jpeg'}))
                arsps.add(API_HOST, endpoint, 'get',
                          aresponses.Response(status=200,
                                              text="What a purdy picture",
                                              headers={'content-type': 'image/jpeg'}))

                # I am of course cheating here by returning text instead of an image
                # for image requests. get_image trusts that the Logi API will always
                # return a valid image for these requests so I don't want to overcomplicate
                # the test.

                # Test return of image
                img = await test_camera.live_stream.get_jpeg()
                self.assertEqual(img, b"Look ma I'm an image")

                # Test download of image to disk
                await test_camera.live_stream.get_jpeg(filename=TEMP_IMAGE)
                with open(TEMP_IMAGE, 'r') as test_file:
                    data = test_file.read()
                    self.assertEqual(data, "What a purdy picture")

        self.loop.run_until_complete(run_test())

    def test_get_image_params(self):
        """Test handling of quality and refresh parameters"""

        gen1_fixture = json.loads(self.fixtures['accessories'])[0]
        test_camera = Camera(self.logi, gen1_fixture)
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, test_camera.id, LIVE_IMAGE_ENDPOINT)

        # Spy on fetch requests
        self.logi._fetch = MagicMock(
            return_value=async_return(FakeStream()))

        async def run_test():
            # Test defaults
            await test_camera.live_stream.get_jpeg()

            self.logi._fetch.assert_called_with(
                headers=ACCEPT_IMAGE_HEADER,
                params={'quality': DEFAULT_IMAGE_QUALITY,
                        'refresh': str(DEFAULT_IMAGE_REFRESH).lower()},
                raw=True,
                url=endpoint)

            # Test quality
            await test_camera.live_stream.get_jpeg(quality=55)
            self.logi._fetch.assert_called_with(
                headers=ACCEPT_IMAGE_HEADER,
                params={'quality': 55,
                        'refresh': str(DEFAULT_IMAGE_REFRESH).lower()},
                raw=True,
                url=endpoint)

            await test_camera.live_stream.get_jpeg(refresh=True)
            self.logi._fetch.assert_called_with(
                headers=ACCEPT_IMAGE_HEADER,
                params={'quality': DEFAULT_IMAGE_QUALITY,
                        'refresh': 'true'},
                raw=True,
                url=endpoint)

        self.loop.run_until_complete(run_test())

    def test_get_rtsp_url(self):
        """Test retrieval of RTSP URL"""

        gen1_fixture = json.loads(self.fixtures['accessories'])[0]
        test_camera = Camera(self.logi, gen1_fixture)
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, test_camera.id, RTSP_ENDPOINT)
        expected_rtsp_uri = json.loads(self.fixtures['rtsp_uri'])['rtsp_uri'].replace('rtsp:', 'rtsps:')

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'get',
                          aresponses.Response(status=200,
                                              text=self.fixtures['rtsp_uri'],
                                              headers={'content-type': 'application/json'}))

                rtsp_uri = await test_camera.live_stream.get_rtsp_url()
                self.assertEqual(expected_rtsp_uri, rtsp_uri)

        self.loop.run_until_complete(run_test())
