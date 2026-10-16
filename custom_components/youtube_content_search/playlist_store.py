"""Persist local playlists; related: __init__.py, services.py, services.yaml."""
import asyncio
from copy import deepcopy
import json
import logging
import re

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STORAGE_KEY = f"{DOMAIN}.playlists"
DATA_PLAYLIST_STORE = "playlist_store"
_ENTITY_PREFIX = f"{DOMAIN}._playlist_"


class PlaylistStore:
    """Serialize durable mutations and expose playlists through existing HA states."""

    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, 1, STORAGE_KEY, atomic_writes=True)
        self.lock = asyncio.Lock()
        self.playlists = {}
        self.closed = False

    @staticmethod
    def _validate(playlists):
        """Reject malformed data instead of overwriting a recoverable store."""
        if not isinstance(playlists, dict):
            raise HomeAssistantError("Invalid playlist storage; restore from backup")
        for name, videos in playlists.items():
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_]+", name):
                raise HomeAssistantError("Invalid playlist storage; restore from backup")
            if not isinstance(videos, list) or any(
                not isinstance(video, dict)
                or not isinstance(video.get("videoId"), str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video["videoId"])
                for video in videos
            ):
                raise HomeAssistantError("Invalid playlist storage; restore from backup")
        return deepcopy(playlists)

    # Restore persisted data first; import legacy states only when no store exists.
    async def async_load(self):
        async with self.lock:
            data = await self.store.async_load()
            if data is not None:
                if not isinstance(data, dict) or "playlists" not in data:
                    raise HomeAssistantError("Invalid playlist storage; restore from backup")
                playlists = self._validate(data["playlists"])
            else:
                playlists = {}
                for state in self.hass.states.async_all():
                    if not state.entity_id.startswith(_ENTITY_PREFIX):
                        continue
                    name = state.entity_id[len(_ENTITY_PREFIX):]
                    try:
                        videos = state.attributes.get("data", "[]")
                        if isinstance(videos, str):
                            videos = json.loads(videos)
                        playlists.update(self._validate({name: videos}))
                    except (ValueError, HomeAssistantError):
                        _LOGGER.warning("Skipping an invalid legacy playlist state")
                if playlists:
                    await self._async_save(playlists)
            self.playlists = playlists
            for name, videos in playlists.items():
                self._publish(name, videos)
            _LOGGER.info("Restored %d local playlists", len(playlists))

    async def _async_save(self, playlists):
        """Use atomic writes and verify data before publishing a mutation."""
        payload = {"playlists": playlists}
        try:
            await self.store.async_save(payload)
            # Store logs some write errors internally; a reload detects an unchanged file.
            if await self.store.async_load() != payload:
                raise HomeAssistantError("Playlist storage verification failed")
        except (OSError, HomeAssistantError):
            raise HomeAssistantError("Unable to save or verify playlist storage") from None

    def _publish(self, name, videos):
        self.hass.states.async_set(
            f"{_ENTITY_PREFIX}{name}", "on", {"data": json.dumps(videos)},
        )

    # Commit before publishing state; the lock covers merge, disk write and state update.
    async def async_merge(self, name, videos):
        async with self.lock:
            if self.closed:
                raise HomeAssistantError("Playlist storage was unloaded; try again after setup")
            playlists = deepcopy(self.playlists)
            merged = {video["videoId"]: video for video in playlists.get(name, [])}
            merged.update({video["videoId"]: video for video in videos})
            playlists[name] = list(merged.values())
            await self._async_save(playlists)
            self.playlists = playlists
            self._publish(name, playlists[name])

    async def async_delete(self, name):
        async with self.lock:
            if self.closed:
                raise HomeAssistantError("Playlist storage was unloaded; try again after setup")
            playlists = deepcopy(self.playlists)
            playlists.pop(name, None)
            await self._async_save(playlists)
            self.playlists = playlists
            self.hass.states.async_remove(f"{_ENTITY_PREFIX}{name}")

    async def async_clear_states(self):
        """Drain mutations on unload and prevent stale writes after a reload."""
        async with self.lock:
            self.closed = True
            for name in self.playlists:
                self.hass.states.async_remove(f"{_ENTITY_PREFIX}{name}")
