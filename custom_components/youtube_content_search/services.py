import aiohttp
import logging
import json 
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant):
    async def async_search_play(call: ServiceCall):
        api_key = hass.data[DOMAIN].get(CONF_API_KEY)
        query = call.data.get("query")
        entity_id = call.data.get("entity_id")

        if not api_key or not query or not entity_id:
            _LOGGER.error("Missing required parameters for search_play service")
            return

        url = (
            f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&type=video,playlist&maxResults=1&q={query}&key={api_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        _LOGGER.error("YouTube API error: %s", resp.status)
                        return
                    data = await resp.json()

            if "items" in data and len(data["items"]) > 0:
                item = data["items"][0]
                id_info = item["id"]

                # videoId 또는 playlistId 구분
                if "videoId" in id_info:
                    media_id = id_info["videoId"]
                    app_name = "youtube"
                elif "playlistId" in id_info:
                    media_id = id_info["playlistId"]
                    app_name = "youtube"  # Cast는 동일하게 youtube 앱 호출
                else:
                    _LOGGER.warning("No valid videoId or playlistId found")
                    return

                cast_payload = {
                    "app_name": app_name,
                    "media_id": media_id
                }

                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": entity_id,
                        "media_content_type": "cast",
                        "media_content_id": json.dumps(cast_payload)
                    },
                )
            else:
                _LOGGER.warning("No YouTube results found for query: %s", query)

        except Exception as e:
            _LOGGER.exception("Error during YouTube search: %s", e)

    # 서비스 등록
    hass.services.async_register(DOMAIN, "search_play", async_search_play)
    return True