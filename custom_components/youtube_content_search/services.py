"""YouTube Content Search - 서비스 및 HTTP 처리 모듈."""

import asyncio
import json as _json_module
import aiohttp
import aiohttp.web
import logging
import urllib.parse
import re
import voluptuous as vol
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from typing import Any, Optional
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN, CONF_API_KEY
from .playlist_store import DATA_PLAYLIST_STORE

_LOGGER = logging.getLogger(__name__)


def _get_api_key(hass: HomeAssistant) -> Optional[str]:
    """Retrieve API key safely from hass.data."""
    config = hass.data.get(DOMAIN, {})
    if isinstance(config, dict):
        return config.get(CONF_API_KEY)
    # Also try entry data (for setup_entry path)
    if "api_key" in hass.data and isinstance(hass.data["api_key"], str):
        return hass.data["api_key"]
    return None


def _sanitize_entity_id(playlist_id: str) -> Optional[str]:
    """Sanitize playlist_id for use as an HA entity ID."""
    # Use valid HA object IDs; related: service playlist save/delete actions.
    sanitized = re.sub(r"[^a-z0-9_]", "_", playlist_id.strip().lower())
    return sanitized if sanitized.strip("_") else None


# ──────────────────────────── REST API Handlers (HTTP Endpoints) ────────────

async def async_handle_youtube_search(hass: HomeAssistant, request: aiohttp.web.Request) -> Any:
    """Handle /youtube-search POST from web UI."""
    api_key = _get_api_key(hass)
    if not api_key:
        return aiohttp.web.json_response({"error": "API key not configured"}, status=401)

    try:
        if request.content_type == 'application/json':
            query_body = await request.json() or {}
            q = query_body.get("query", "")
            max_results = int(query_body.get("maxResults", 15))
        else:
            raw_text = (await request.text()).strip()
            q = urllib.parse.unquote(raw_text)
            max_results = 15

    except Exception as e:
        return aiohttp.web.json_response({"error": "Invalid request body"}, status=400)

    if not q or not isinstance(q, str):
        return aiohttp.web.json_response({"error": "Empty query"}, status=400)

    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&type=video&maxResults={max_results}&q={urllib.parse.quote(q)}&key={api_key}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    _LOGGER.error("YouTube API error: %s", resp.status)
                    return aiohttp.web.json_response({"error": f"API error {resp.status}"}, status=500)
                data = await resp.json()

    except Exception as e:
        _LOGGER.exception("Error during YouTube search response fetch: %s", e)
        return aiohttp.web.json_response({"error": str(e)}, status=500)

    items = data.get("items") or []
    videos = []
    for item in items:
        vid = item.get("id", {})
        video_id = vid.get("videoId", "")
        if not video_id:
            continue

        thm_data = []
        ths = (item.get("snippet") or {}).get("thumbnails") or {}
        for size_name in ["default", "medium", "high", "maxres"]:
            if size_name in ths:
                th_info = ths[size_name]
                url_val = th_info["url"] if isinstance(th_info, dict) else (str(th_info) if th_info else "")
                thm_data.append({
                    "width": None,
                    "height": None,
                    "url": url_val or ""
                })

        videos.append({
            "id": video_id,
            "title": (item.get("snippet") or {}).get("title") or "",
            "description": (item.get("snippet") or {}).get("description") or "",
            "channelName": (item.get("snippet") or {}).get("channelTitle") or "",
            "duration": None,
            "thumbnails": thm_data,
        })

    return aiohttp.web.json_response({"results": videos})


async def async_handle_playlist_detail(hass: HomeAssistant, request: aiohttp.web.Request) -> Any:
    """Handle /playlist-detail/{id} GET from web UI."""
    api_key = _get_api_key(hass)
    if not api_key:
        return aiohttp.web.json_response({"error": "API key not configured"}, status=401)

    try:
        playlist_id = request.match_info["playlist_id"]
    except KeyError as e:
        _LOGGER.error("Missing playlist_id in URL path: %s", e)
        return aiohttp.web.json_response({"error": "Playlist ID not found"}, status=400)

    # Fetch videos from the playlist via YouTube Data API v3 playlists.list + items.list
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://www.googleapis.com/youtube/v3/playlists?part=id&playlistId={playlist_id}&key={api_key}"
            async with session.get(url) as resp:
                if resp.status != 200:
                    _LOGGER.error("YouTube API playlist error: %s", resp.status)
                    return aiohttp.web.json_response({"error": f"API error {resp.status}"}, status=500)

            pl_data = await resp.json()
            items_list = [i["id"] for i in (pl_data.get("items") or [])]

    except Exception as e:
        _LOGGER.exception("Error fetching playlist info: %s", e)
        return aiohttp.web.json_response({"error": str(e)}, status=500)

    if not items_list:
        return aiohttp.web.json_response({"playlist_id": playlist_id, "videos": []})

    # Fetch individual video IDs via search
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&id={','.join(items_list)}&type=video&key={api_key}"
            async with session.get(url) as resp:
                if resp.status != 200:
                    _LOGGER.error("YouTube API search error: %s", resp.status)
                    return aiohttp.web.json_response({"error": f"API error {resp.status}"}, status=500)

            data = await resp.json()
            items = data.get("items") or []
            videos = []
            for item in items:
                vid = item.get("id", {})
                video_id = vid.get("videoId", "") if isinstance(vid, dict) else str(vid)

                thm_data = []
                ths = (item.get("snippet") or {}).get("thumbnails") or {}
                for size_name in ["default", "medium", "high"]:
                    if size_name in ths:
                        th_info = ths[size_name]
                        url_val = th_info.get("url") if isinstance(th_info, dict) else (str(th_info) if th_info else "")
                        thm_data.append({
                            "width": None,
                            "height": None,
                            "url": url_val or ""
                        })

                videos.append({
                    "videoId": video_id,
                    "title": item.get("snippet", {}).get("title") or "",
                    "channel": (item.get("snippet") or {}).get("channelTitle") or "",
                    "thumbnail": thm_data,
                })

            return aiohttp.web.json_response({"playlist_id": playlist_id, "videos": videos})

    except Exception as e:
        _LOGGER.exception("Error fetching video details for playlist %s: %s", playlist_id, e)
        return aiohttp.web.json_response({"error": str(e)}, status=500)


async def async_handle_playlist_save(hass: HomeAssistant, request: aiohttp.web.Request) -> Any:
    """Handle /playlist-save POST from web UI (add videos to a playlist)."""

    try:
        data = await request.json() if request.content_type == 'application/json' else {}
        video_ids_str = data.get("video_ids", []) or []
        playlist_id = data.get("playlist_id")
    except Exception as e:
        return aiohttp.web.json_response({"error": "Invalid request body"}, status=400)

    if not playlist_id:
        _LOGGER.error("Missing playlist_id for playlist_save.")
        return aiohttp.web.json_response({"error": "Playlist ID required"}, status=400)

    try:
        video_ids = [str(v).strip() for v in (video_ids_str or [])]

        sanitized_playlist_id = _sanitize_entity_id(str(playlist_id))
        if not sanitized_playlist_id:
            _LOGGER.error("Invalid playlist_id for playlist_save: %s", playlist_id)
            return aiohttp.web.json_response({"error": "Invalid playlist ID"}, status=400)
        entity_id = f"youtube_content_search._playlist_{sanitized_playlist_id}"

        # Get current state data
        new_videos = []
        existing_videos = {}

        states = hass.states.async_all()
        for s in states:
            if s.entity_id == entity_id:
                try:
                    raw_data = (s.attributes or {}).get('data', '[]')
                    parsed = _json_module.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    existing_videos = {v['videoId']: v for v in (parsed or [])}
                    new_videos = list(parsed or [])
                except Exception:
                    pass

        # Add new video IDs that aren't already present
        for vid_id in video_ids:
            if vid_id not in existing_videos:
                existing_videos[vid_id] = {
                    'videoId': vid_id,
                    'title': '',
                    'channel': ''
                }

        updated_list = list(existing_videos.values())
        hass.states.async_set(entity_id, 'on', {'data': _json_module.dumps(updated_list)})

        _LOGGER.info("Playlist save: added %d videos to '%s'", len(video_ids) - sum(1 for v in video_ids if v in existing_videos), playlist_id)

    except Exception as e:
        _LOGGER.exception("Error saving to playlist %s: %s", playlist_id, e)
        return aiohttp.web.json_response({"error": str(e)}, status=500)


async def async_handle_playlist_delete(hass: HomeAssistant, request: aiohttp.web.Request) -> Any:
    """Handle /playlist-delete/{id} DELETE from web UI."""

    try:
        playlist_id = request.match_info["playlist_id"]
        sanitized_playlist_id = _sanitize_entity_id(str(playlist_id))
        if not sanitized_playlist_id:
            _LOGGER.error("Invalid playlist_id for playlist_delete: %s", playlist_id)
            return aiohttp.web.json_response({"error": "Invalid playlist ID"}, status=400)
        entity_id = f"youtube_content_search._playlist_{sanitized_playlist_id}"
        hass.states.async_remove(entity_id)
        return aiohttp.web.json_response({"success": True, "message": f"Playlist '{playlist_id}' deleted"})

    except Exception as e:
        _LOGGER.exception("Error deleting playlist %s: %s", playlist_id, e)
        return aiohttp.web.json_response({"error": str(e)}, status=500)


# ──────────────────────────── Service Functions (Cast Playback / Legacy Mode) ────────────

# Service-only actions use HA's shared HTTP session; related: __init__.py/services.yaml.
def _require_api_key(hass: HomeAssistant) -> str:
    api_key = _get_api_key(hass)
    if not api_key:
        raise ServiceValidationError("Configure YouTube Content Search before calling this action")
    return api_key


# Only known constant codes may enter errors; related: tests/test_service_only.py and README.md.
_SAFE_API_ERROR_CODES = frozenset({
    "API_KEY_INVALID", "API_KEY_SERVICE_BLOCKED", "API_KEY_HTTP_REFERRER_BLOCKED",
    "API_KEY_IP_ADDRESS_BLOCKED", "API_KEY_ANDROID_APP_BLOCKED", "API_KEY_IOS_APP_BLOCKED",
    "SERVICE_DISABLED", "BILLING_DISABLED", "CONSUMER_INVALID",
    "INVALID_ARGUMENT", "PERMISSION_DENIED", "UNAUTHENTICATED", "RESOURCE_EXHAUSTED",
    "badRequest", "keyInvalid", "accessNotConfigured", "forbidden", "quotaExceeded",
    "dailyLimitExceeded", "rateLimitExceeded", "incompatibleParameters", "invalidFilters",
    "invalidPageToken", "missingRequiredParameter", "unexpectedParameter", "invalidValue",
    "invalidPart", "unexpectedPart", "unknownPart", "invalidSearchFilter",
})


def _safe_api_error_codes(payload) -> str:
    """Read structured reasons while discarding messages, metadata and unknown strings."""
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return "UNKNOWN"
    codes = []
    for field in ("details", "errors"):
        entries = error.get(field, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            reason = entry.get("reason") if isinstance(entry, dict) else None
            if isinstance(reason, str) and reason in _SAFE_API_ERROR_CODES and reason not in codes:
                codes.append(reason)
    status = error.get("status")
    if isinstance(status, str) and status in _SAFE_API_ERROR_CODES and status not in codes:
        codes.append(status)
    return ", ".join(codes) if codes else "UNKNOWN"


async def _async_youtube_request(hass: HomeAssistant, resource: str, params: dict) -> dict:
    """Request API data without exposing credential-bearing URLs in errors."""
    params = {**params, "key": _require_api_key(hass)}
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"https://www.googleapis.com/youtube/v3/{resource}",
            params=params, timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                # Parse only approved reason codes; never expose response text or request URLs.
                try:
                    payload = await response.json()
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                    payload = None
                reasons = _safe_api_error_codes(payload)
                raise HomeAssistantError(
                    f"YouTube API returned HTTP {response.status} (reason: {reasons})"
                ) from None
            return await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        raise HomeAssistantError("Unable to retrieve YouTube data") from None


# Share Cast identity checks with Assist; related: llm.py and services.yaml.
def is_cast_player(hass: HomeAssistant, entity_id: str) -> bool:
    """Allow only media players registered by the Google Cast integration."""
    if not entity_id.startswith("media_player."):
        return False
    entry = er.async_get(hass).async_get(entity_id)
    return entry is not None and entry.platform == "cast"


# Validate Cast targets before API requests; related: llm.py/services.yaml.
async def async_search_play(hass: HomeAssistant, call: ServiceCall):
    """Search for one video and play it using Google Cast."""
    query = call.data["query"].strip()
    if not query:
        raise ServiceValidationError("Search query cannot be empty")
    if not is_cast_player(hass, call.data["entity_id"]):
        raise ServiceValidationError("Choose a media player provided by Google Cast")
    data = await _async_youtube_request(hass, "search", {
        "part": "snippet", "type": "video", "maxResults": 1, "q": query,
    })
    items = data.get("items") or []
    if not items or not items[0].get("id", {}).get("videoId"):
        raise HomeAssistantError("No YouTube video found")
    # Cast playback only; related: services.yaml and README.md.
    video_id = items[0]["id"]["videoId"]
    await hass.services.async_call(
        "media_player", "play_media", {
            "entity_id": call.data["entity_id"],
            "media_content_type": "cast",
            "media_content_id": _json_module.dumps({
                "app_name": "youtube", "media_id": video_id,
            }),
        }, blocking=True,
    )


# Normalize list/CSV/JSON inputs consistently; related: services.yaml and README.md.
def _normalize_video_ids(value):
    if isinstance(value, str):
        try:
            parsed = _json_module.loads(value)
        except ValueError:
            parsed = value.split(",")
        value = parsed if isinstance(parsed, list) else value.split(",")
    if not isinstance(value, list) or not value:
        raise vol.Invalid("Provide a non-empty video ID list")
    result = []
    for video_id in value:
        if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id.strip()):
            raise vol.Invalid("Each YouTube video ID must contain 11 valid characters")
        if video_id.strip() not in result:
            result.append(video_id.strip())
    return result


async def async_playlist_save_service(hass: HomeAssistant, call: ServiceCall):
    """Merge videos into a persistent HA playlist, without modifying YouTube."""
    _require_api_key(hass)
    playlist_id = _sanitize_entity_id(call.data["playlist_id"])
    if not playlist_id:
        raise ServiceValidationError("Playlist ID cannot be empty")
    video_ids = call.data["video_ids"]
    video_infos = []
    for offset in range(0, len(video_ids), 50):
        data = await _async_youtube_request(hass, "videos", {
            "part": "snippet", "id": ",".join(video_ids[offset:offset + 50]),
        })
        metadata = {item["id"]: item.get("snippet", {}) for item in data.get("items", [])}
        for video_id in video_ids[offset:offset + 50]:
            snippet = metadata.get(video_id, {})
            thumbnails = snippet.get("thumbnails", {})
            thumbnail = thumbnails.get("medium", thumbnails.get("default", {}))
            video_infos.append({
                "videoId": video_id, "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""), "thumbnail": thumbnail.get("url", ""),
            })
    # Persist mutations under a shared lock; related: playlist_store.py/__init__.py.
    playlists = hass.data.get(DOMAIN, {}).get(DATA_PLAYLIST_STORE)
    if playlists is None:
        raise ServiceValidationError("Playlist storage is not configured")
    await playlists.async_merge(playlist_id, video_infos)


async def async_playlist_delete_service(hass: HomeAssistant, call: ServiceCall):
    """Delete a persistent HA playlist, without modifying YouTube."""
    _require_api_key(hass)
    playlist_id = _sanitize_entity_id(call.data["id"])
    if not playlist_id:
        raise ServiceValidationError("Playlist ID cannot be empty")
    # Persist deletion before removing state; related: playlist_store.py.
    playlists = hass.data.get(DOMAIN, {}).get(DATA_PLAYLIST_STORE)
    if playlists is None:
        raise ServiceValidationError("Playlist storage is not configured")
    await playlists.async_delete(playlist_id)


async def async_setup_services(hass: HomeAssistant):
    """Register validated actions once; related: services.yaml/config_flow.py."""
    async def _search_play(call: ServiceCall):
        await async_search_play(hass, call)

    async def _playlist_save_service(call: ServiceCall):
        await async_playlist_save_service(hass, call)

    async def _playlist_delete_service(call: ServiceCall):
        await async_playlist_delete_service(hass, call)

    actions = {
        "search_play": (_search_play, vol.Schema({
            vol.Required("query"): cv.string,
            vol.Required("entity_id"): vol.All(cv.entity_id, vol.Match(r"^media_player\.")),
        })),
        "playlist_save": (_playlist_save_service, vol.Schema({
            vol.Required("playlist_id"): cv.string,
            vol.Required("video_ids"): _normalize_video_ids,
        })),
        "playlist_delete": (_playlist_delete_service, vol.Schema({vol.Required("id"): cv.string})),
    }
    for name, (handler, schema) in actions.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handler, schema=schema)


async def async_unload_services(hass: HomeAssistant):
    """Unregister legacy service functions."""
    try:
        hass.services.async_remove(DOMAIN, "search_play")
        hass.services.async_remove(DOMAIN, "playlist_save")
        hass.services.async_remove(DOMAIN, "playlist_delete")
    except Exception as err:
        _LOGGER.error("YouTube Content Search services unload failed: %s", err, exc_info=True)
