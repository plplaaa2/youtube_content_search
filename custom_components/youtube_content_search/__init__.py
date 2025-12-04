from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .services import async_setup_services

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # API 키 저장
    hass.data[DOMAIN] = entry.data
    # 서비스 등록
    await async_setup_services(hass)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    # 서비스 언로드
    hass.services.async_remove(DOMAIN, "search_play")
    hass.data.pop(DOMAIN, None)
    return True
