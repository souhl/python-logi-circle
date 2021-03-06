# -*- coding: utf-8 -*-
"""The tests for the Logi API platform."""
from datetime import datetime
import json
import aresponses
from aiohttp.client_exceptions import ClientResponseError
from tests.test_base import LogiUnitTestBase
from logi_circle.camera import Camera
from logi_circle.activity import Activity
from logi_circle.const import (API_HOST,
                               ACCESSORIES_ENDPOINT,
                               ACTIVITIES_ENDPOINT,
                               ACTIVITY_API_LIMIT,
                               CONFIG_ENDPOINT,
                               GEN_1_MODEL,
                               GEN_2_MODEL,
                               GEN_1_MOUNT,
                               GEN_2_MOUNT_WIRE,
                               GEN_2_MOUNT_WIREFREE,
                               MOUNT_UNKNOWN)


class TestCamera(LogiUnitTestBase):
    """Unit test for the Camera class."""

    def setUp(self):
        """Set up Camera class with fixtures"""
        super(TestCamera, self).setUp()

        self.gen1_fixture = json.loads(self.fixtures['accessories'])[0]
        self.test_camera = Camera(self.logi, self.gen1_fixture)
        self.logi.auth_provider = self.get_authorized_auth_provider()

    def tearDown(self):
        """Remove test Camera instance"""
        super(TestCamera, self).tearDown()
        del self.gen1_fixture
        del self.test_camera

    def test_camera_props(self):
        """Camera props should match fixtures"""
        gen1_fixture = self.gen1_fixture

        # Mandatory props
        self.assertEqual(self.test_camera.id, gen1_fixture['accessoryId'])
        self.assertEqual(self.test_camera.name, gen1_fixture['name'])
        self.assertEqual(self.test_camera.mac_address, gen1_fixture['mac'])
        gen1_fixture['cfg'] = gen1_fixture['configuration']

        # Optional props
        self.assertEqual(self.test_camera.model, gen1_fixture['modelNumber'])
        self.assertEqual(self.test_camera.mount, GEN_1_MOUNT)
        self.assertEqual(self.test_camera.connected, gen1_fixture['isConnected'])
        self.assertEqual(self.test_camera.streaming, gen1_fixture['cfg']['streamingEnabled'])
        self.assertEqual(self.test_camera.timezone, gen1_fixture['cfg']['timeZone'])
        self.assertEqual(self.test_camera.battery_level, gen1_fixture['cfg']['batteryLevel'])
        self.assertEqual(self.test_camera.charging, gen1_fixture['cfg']['batteryCharging'])
        self.assertEqual(self.test_camera.battery_saving, gen1_fixture['cfg']['saveBattery'])
        self.assertEqual(self.test_camera.signal_strength_percentage, gen1_fixture['cfg']['wifiSignalStrength'])
        self.assertEqual(self.test_camera.firmware, gen1_fixture['cfg']['firmwareVersion'])
        self.assertEqual(self.test_camera.microphone, gen1_fixture['cfg']['microphoneOn'])
        self.assertEqual(self.test_camera.microphone_gain, gen1_fixture['cfg']['microphoneGain'])
        self.assertEqual(self.test_camera.speaker, gen1_fixture['cfg']['speakerOn'])
        self.assertEqual(self.test_camera.speaker_volume, gen1_fixture['cfg']['speakerVolume'])
        self.assertEqual(self.test_camera.led, gen1_fixture['cfg']['ledEnabled'])
        self.assertEqual(self.test_camera.recording, not gen1_fixture['cfg']['privacyMode'])

    def test_missing_mandatory_props(self):
        """Camera should raise if mandatory props missing"""
        incomplete_camera = {
            "name": "Incomplete cam",
            "accessoryId": "123",
            "configuration": {
                "stuff": "123"
            }
        }

        with self.assertRaises(KeyError):
            Camera(self.logi, incomplete_camera)

    def test_missing_optional_props(self):
        """Camera should not raise if optional props missing"""
        incomplete_camera = {
            "name": "Incomplete cam",
            "accessoryId": "123",
            "mac": "ABC",
            "configuration": {
                "modelNumber": "1234",
                "batteryLevel": 1
            },
            "isConnected": False
        }

        camera = Camera(self.logi, incomplete_camera)
        self.assertEqual(camera.name, "Incomplete cam")
        self.assertEqual(camera.id, "123")
        self.assertEqual(camera.mac_address, "ABC")

        # Optional int/string props not passed to Camera should be None
        self.assertIsNone(camera.charging)
        self.assertIsNone(camera.battery_saving)
        self.assertIsNone(camera.signal_strength_percentage)
        self.assertIsNone(camera.signal_strength_category)
        self.assertIsNone(camera.firmware)
        self.assertIsNone(camera.microphone_gain)
        self.assertIsNone(camera.speaker_volume)

        # Optional bools should be neutral
        self.assertFalse(camera.streaming)
        self.assertFalse(camera.microphone)
        self.assertFalse(camera.speaker)
        self.assertFalse(camera.led)
        self.assertTrue(camera.recording)

        # Timezone should fallback to UTC
        self.assertEqual(camera.timezone, "UTC")

        # Mount should be unknown
        self.assertEqual(camera.mount, MOUNT_UNKNOWN)

    def test_camera_mount_prop(self):
        """Test mount property correctly infers type from other props"""

        gen2_wired_fixture = json.loads(self.fixtures['accessories'])[1]
        gen2_wirefree_fixture = json.loads(self.fixtures['accessories'])[2]

        gen1_camera = Camera(self.logi, self.gen1_fixture)
        gen2_wired_camera = Camera(self.logi, gen2_wired_fixture)
        gen2_wirefree_camera = Camera(self.logi, gen2_wirefree_fixture)

        # Test 1st gen
        self.assertEqual(gen1_camera.mount, GEN_1_MOUNT)
        self.assertEqual(gen1_camera.model, GEN_1_MODEL)

        # Test 2nd gen wired camera (should have no battery)
        self.assertEqual(gen2_wired_camera.mount, GEN_2_MOUNT_WIRE)
        self.assertEqual(gen2_wired_camera.battery_level, -1)
        self.assertEqual(gen2_wired_camera.model, GEN_2_MODEL)

        # Test 2nd gen wire-free camera (should have battery)
        self.assertEqual(gen2_wirefree_camera.mount, GEN_2_MOUNT_WIREFREE)
        self.assertNotEqual(gen2_wirefree_camera.battery_level, -1)
        self.assertEqual(gen2_wirefree_camera.model, GEN_2_MODEL)

    def test_signal_strength_categories(self):
        """Test friendly signal strength categorisation"""

        self.test_camera._attrs['signal_strength_percentage'] = 99
        self.assertEqual(self.test_camera.signal_strength_category, 'Excellent')

        self.test_camera._attrs['signal_strength_percentage'] = 79
        self.assertEqual(self.test_camera.signal_strength_category, 'Good')

        self.test_camera._attrs['signal_strength_percentage'] = 59
        self.assertEqual(self.test_camera.signal_strength_category, 'Fair')

        self.test_camera._attrs['signal_strength_percentage'] = 39
        self.assertEqual(self.test_camera.signal_strength_category, 'Poor')

        self.test_camera._attrs['signal_strength_percentage'] = 19
        self.assertEqual(self.test_camera.signal_strength_category, 'Bad')

        self.test_camera._attrs['signal_strength_percentage'] = None
        self.assertIsNone(self.test_camera.signal_strength_category)

    def test_update(self):
        """Test polling for changes in camera properties"""
        endpoint = '%s/%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'get',
                          aresponses.Response(status=200,
                                              text=self.fixtures['accessory'],
                                              headers={'content-type': 'application/json'}))
                # Props should match fixture
                self.assertEqual(self.test_camera.battery_level, 100)
                self.assertEqual(self.test_camera.signal_strength_percentage, 74)

                await self.test_camera.update()
                # Props should have changed.
                self.assertEqual(self.test_camera.battery_level, 99)
                self.assertEqual(self.test_camera.signal_strength_percentage, 88)

        self.loop.run_until_complete(run_test())

    def test_set_config_valid(self):
        """Test updating configuration for camera"""
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id, CONFIG_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'put',
                          aresponses.Response(status=200))
                arsps.add(API_HOST, endpoint, 'put',
                          aresponses.Response(status=200))
                arsps.add(API_HOST, endpoint, 'put',
                          aresponses.Response(status=200))

                # Set streaming enabled property
                self.assertEqual(self.test_camera.streaming, True)

                # Prop should change when config successfully updated
                await self.test_camera.set_config('streaming', False)
                self.assertEqual(self.test_camera.streaming, False)

                # Disable recording
                self.assertEqual(self.test_camera.recording, True)

                # Prop should change when config successfully updated
                await self.test_camera.set_config('recording_disabled', True)
                self.assertEqual(self.test_camera.recording, False)

                # Enable recording

                # Prop should change when config successfully updated
                await self.test_camera.set_config('recording_disabled', False)
                self.assertEqual(self.test_camera.recording, True)

        self.loop.run_until_complete(run_test())

    def test_set_config_error(self):
        """Test updating configuration for camera"""
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id, CONFIG_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'put',
                          aresponses.Response(status=500))

                self.assertEqual(self.test_camera.streaming, True)

                # Prop should not update if PUT request fails
                with self.assertRaises(ClientResponseError):
                    await self.test_camera.set_config('streaming', False)
                self.assertEqual(self.test_camera.streaming, True)

        self.loop.run_until_complete(run_test())

    def test_set_config_invalid(self):
        """Test updating invalid configuration prop for camera"""

        async def run_test():
            # Read-only prop
            with self.assertRaises(NameError):
                await self.test_camera.set_config('firmware', 'Windows 95')

            # Non-existent prop
            with self.assertRaises(NameError):
                await self.test_camera.set_config('nonsense', 123)

        self.loop.run_until_complete(run_test())

    def test_get_last_activity(self):
        """Test get last activity property"""
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id, ACTIVITIES_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'post',
                          aresponses.Response(status=200,
                                              text=self.fixtures['activities'],
                                              headers={'content-type': 'application/json'}))
                # Props should match fixture
                self.assertIsInstance(await self.test_camera.get_last_activity(), Activity)

        self.loop.run_until_complete(run_test())

    def test_no_last_activity(self):
        """Test last_activity property when no activities reported from server"""
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id, ACTIVITIES_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'post',
                          aresponses.Response(status=200,
                                              text='{ "activities" : [] }',
                                              headers={'content-type': 'application/json'}))
                # Props should match fixture
                self.assertIsNone(await self.test_camera.get_last_activity())

        self.loop.run_until_complete(run_test())

    def test_query_activity_history(self):
        """Test get last activity property"""
        endpoint = '%s/%s%s' % (ACCESSORIES_ENDPOINT, self.test_camera.id, ACTIVITIES_ENDPOINT)

        async def run_test():
            async with aresponses.ResponsesMockServer(loop=self.loop) as arsps:
                arsps.add(API_HOST, endpoint, 'post',
                          aresponses.Response(status=200,
                                              text=self.fixtures['activities'],
                                              headers={'content-type': 'application/json'}))
                activities = await self.test_camera.query_activity_history(
                    property_filter='prop_filter',
                    date_filter=datetime.now(),
                    date_operator='>',
                    limit=100
                )
                self.assertIsInstance(activities, list)
                for activity in activities:
                    self.assertIsInstance(activity, Activity)

        self.loop.run_until_complete(run_test())

    def test_activity_api_limits(self):
        """Test requesting more activities then API permits"""

        async def run_test():
            with self.assertRaises(ValueError):
                await self.test_camera.query_activity_history(limit=ACTIVITY_API_LIMIT + 1)

        self.loop.run_until_complete(run_test())

    def test_activity_reject_bad_type(self):
        """Test rejection of date filter if it's not a datetime object"""

        async def run_test():
            with self.assertRaises(TypeError):
                await self.test_camera.query_activity_history(date_filter='2018-01-01')

        self.loop.run_until_complete(run_test())

    def test_slugify_safe_name(self):
        """Returns camera ID if camera name string empty after slugification."""

        valid_name = 'My camera'
        invalid_name = '!@#$%^&*()'

        # Test valid name
        self.test_camera._attrs['name'] = valid_name
        self.assertEqual(self.test_camera.slugify_safe_name, valid_name)

        # Test invalid name
        self.test_camera._attrs['name'] = invalid_name
        self.assertEqual(self.test_camera.slugify_safe_name, self.test_camera.id)

        # Test whitespace
        self.test_camera._attrs['name'] = ' '
        self.assertEqual(self.test_camera.slugify_safe_name, self.test_camera.id)

        # Test empty name
        self.test_camera._attrs['name'] = ''
        self.assertEqual(self.test_camera.slugify_safe_name, self.test_camera.id)
