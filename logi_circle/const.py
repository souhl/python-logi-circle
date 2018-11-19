# coding: utf-8
# vim:sw=4:ts=4:et:
"""Constants"""
import os

try:
    DEFAULT_CACHE_FILE = os.path.join(
        os.getenv("HOME"), '.logi_circle-session.cache')
except (AttributeError, TypeError):
    DEFAULT_CACHE_FILE = os.path.join('.', '.logi_circle-session.cache')

# OAuth2 constants
AUTH_HOST = "accounts.logi.com"
AUTH_BASE = "https://%s" % (AUTH_HOST)
AUTH_ENDPOINT = "/identity/oauth2/authorize"
TOKEN_ENDPOINT = "/identity/oauth2/token"
DEFAULT_SCOPES = ("circle:activities_basic circle:activities circle:accessories circle:accessories_ro "
                  "circle:live_image circle:live circle:notifications circle:summaries")

# API endpoints
API_HOST = "api.circle.logi.com"
API_BASE = "https://%s" % (API_HOST)
ACCESSORIES_ENDPOINT = "/api/accessories"
CONFIG_ENDPOINT = "/config"
LIVE_IMAGE_ENDPOINT = "/live/image"
RTSP_ENDPOINT = "/live/rtsp"

# Headers
ACCEPT_IMAGE_HEADER = {'Accept': 'image/jpeg'}

# Misc
DEFAULT_IMAGE_QUALITY = 75
DEFAULT_IMAGE_REFRESH = False

# Prop to API mapping
PROP_MAP = {
    "id": {"key": "accessoryId", "required": True},
    "name": {"key": "name", "required": True, "settable": True},
    "mac_address": {"key": "mac", "required": True},
    "is_connected": {"key": "isConnected", "default_value": False},
    "model": {"key": "modelNumber"},
    "streaming_enabled": {"key": "streamingEnabled", "config": True, "default_value": False, "settable": True},
    "is_charging": {"key": "batteryCharging", "config": True},
    "battery_saving": {"key": "saveBattery", "config": True},
    "timezone": {"key": "timeZone", "config": True, "default_value": "UTC", "settable": True},
    "battery_level": {"key": "batteryLevel", "config": True, "default_value": -1},
    "signal_strength_percentage": {"key": "wifiSignalStrength", "config": True},
    "firmware": {"key": "firmwareVersion", "config": True},
    "microphone_on": {"key": "microphoneOn", "config": True, "default_value": False},
    "microphone_gain": {"key": "microphoneGain", "config": True},
    "speaker_on": {"key": "speakerOn", "config": True, "default_value": False},
    "speaker_volume": {"key": "speakerVolume", "config": True},
    "led_on": {"key":  "ledEnabled", "config": True, "default_value": False},
    "privacy_mode": {"key":  "privacyMode", "config": True, "default_value": False, "settable": True}
}
