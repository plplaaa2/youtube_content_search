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
from .const import (
    CONF_API_KEY, CONF_PLAYBACK_MODE, DEFAULT_PLAYBACK_MODE, DOMAIN,
    PLAYBACK_MODE_APP_LINKS, PLAYBACK_MODE_CAST, PLAYBACK_MODE_SMARTTUBE,
    PLAYBACK_MODE_CAST_FALLBACK,
)

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


# Validate Android TV Remote targets independently; related: llm.py/config_flow.py.
def is_app_link_player(hass: HomeAssistant, entity_id: str) -> bool:
    """Allow only remote entities registered by Android TV Remote."""
    if not entity_id.startswith("remote."):
        return False
    entry = er.async_get(hass).async_get(entity_id)
    return entry is not None and entry.platform == "androidtv_remote"


def playback_mode(hass: HomeAssistant) -> str:
    """Return the configured mode, preserving Cast for older entries."""
    config = hass.data.get(DOMAIN, {})
    if isinstance(config, dict):
        return config.get(CONF_PLAYBACK_MODE, DEFAULT_PLAYBACK_MODE)
    return DEFAULT_PLAYBACK_MODE


def _video_id_from_input(value: str) -> str:
    """Accept an 11-character YouTube video ID or a supported video URL."""
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    try:
        parsed = urllib.parse.urlsplit(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https"):
            raise ValueError
        if host == "youtu.be":
            candidate = parsed.path.strip("/").split("/")[0]
        elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
            parts = [part for part in parsed.path.split("/") if part]
            if parsed.path == "/watch":
                candidate = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
            elif len(parts) == 2 and parts[0] in {"shorts", "embed", "live"}:
                candidate = parts[1]
            else:
                raise ValueError
        else:
            raise ValueError
    except (ValueError, UnicodeError):
        raise ServiceValidationError("Provide a YouTube video URL or 11-character video ID") from None
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise ServiceValidationError("Provide a YouTube video URL or 11-character video ID")
    return candidate


# Validate selected playback targets before API requests; related: llm.py/services.yaml.
async def async_search_play(hass: HomeAssistant, call: ServiceCall):
    """Search for or directly select one video and dispatch via configured playback mode."""
    query = (call.data.get("query") or "").strip()
    video = (call.data.get("video") or "").strip()
    if bool(query) == bool(video):
        raise ServiceValidationError("Provide exactly one of a search query or video URL/ID")
    mode = playback_mode(hass)
    app_link_mode = mode in (PLAYBACK_MODE_APP_LINKS + (PLAYBACK_MODE_CAST_FALLBACK,))
    valid_target = is_app_link_player(hass, call.data["entity_id"]) if app_link_mode else is_cast_player(hass, call.data["entity_id"])
    if not valid_target:
        message = "Choose a remote provided by Android TV Remote" if app_link_mode else "Choose a media player provided by Google Cast"
        raise ServiceValidationError(message)
    if video:
        video_id = _video_id_from_input(video)
    else:
        data = await _async_youtube_request(hass, "search", {
            "part": "snippet", "type": "video", "maxResults": 1, "q": query,
        })
        items = data.get("items") or []
        if not items or not items[0].get("id", {}).get("videoId"):
            raise HomeAssistantError("No YouTube video found")
        video_id = items[0]["id"]["videoId"]
    if app_link_mode:
        activity = f"https://www.youtube.com/watch?v={video_id}"
        if mode in (PLAYBACK_MODE_SMARTTUBE, PLAYBACK_MODE_CAST_FALLBACK):
            activity = f"vnd.youtube.launch://www.youtube.com/watch?v={video_id}"
        try:
            await hass.services.async_call(
                "remote", "turn_on", {
                    "entity_id": call.data["entity_id"],
                    "activity": activity,
                }, blocking=True,
            )
            return
        except HomeAssistantError:
            if mode not in (PLAYBACK_MODE_APP_LINKS + (PLAYBACK_MODE_CAST_FALLBACK,)):
                raise
            cast_entity = call.data.get("cast_entity_id")
            if not cast_entity or not is_cast_player(hass, cast_entity):
                raise ServiceValidationError(
                    "App-link playback failed; configure a valid Cast fallback entity"
                ) from None
            _LOGGER.warning("Android TV app-link playback failed; trying Google Cast fallback")
            await _async_cast_play(hass, cast_entity, video_id)
            return
    await _async_cast_play(hass, call.data["entity_id"], video_id)


# Keep Cast dispatch shared by the direct and fallback playback paths; related: async_search_play.
async def _async_cast_play(hass: HomeAssistant, entity_id: str, video_id: str) -> None:
    """Send a YouTube Cast request for one validated video ID."""
    await hass.services.async_call(
        "media_player", "play_media", {
            "entity_id": entity_id,
            "media_content_type": "cast",
            "media_content_id": _json_module.dumps({
                "app_name": "youtube", "media_id": video_id,
            }),
        }, blocking=True,
    )


async def async_setup_services(hass: HomeAssistant):
    """Register the validated YouTube playback action; related: services.yaml/config_flow.py."""
    async def _search_play(call: ServiceCall):
        await async_search_play(hass, call)

    actions = {
        "search_play": (_search_play, vol.Schema({
            vol.Optional("query"): cv.string,
            vol.Optional("video"): cv.string,
            vol.Required("entity_id"): cv.entity_id,
            vol.Optional("cast_entity_id"): vol.All(cv.entity_id, vol.Match(r"^media_player\.")),
        })),
    }
    for name, (handler, schema) in actions.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handler, schema=schema)


async def async_unload_services(hass: HomeAssistant):
    """Unregister the YouTube playback action."""
    try:
        hass.services.async_remove(DOMAIN, "search_play")
    except Exception as err:
        _LOGGER.error("YouTube Content Search service unload failed: %s", err, exc_info=True)
