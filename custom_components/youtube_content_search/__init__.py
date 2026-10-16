"""Set up service-only YouTube Content Search."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_API_KEY, DOMAIN
from .playlist_store import DATA_PLAYLIST_STORE, PlaylistStore
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)


# Load entry credentials for services.py; no frontend or HTTP routes are registered.
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Load the credentials used by service actions."""
    api_key = config_entry.options.get(CONF_API_KEY, config_entry.data.get(CONF_API_KEY))
    if not isinstance(api_key, str) or not api_key.strip():
        raise ConfigEntryError("YouTube API key is required")
    # Restore local playlists before enabling actions; related: playlist_store.py.
    runtime = hass.data.setdefault(DOMAIN, {})
    if DATA_PLAYLIST_STORE not in runtime:
        playlists = PlaylistStore(hass)
        await playlists.async_load()
        runtime[DATA_PLAYLIST_STORE] = playlists
    hass.data.setdefault(DOMAIN, {})[CONF_API_KEY] = api_key.strip()
    # Register a selectable LLM tool provider on every supported HA; related: llm.py.
    from .llm import async_register_api

    async_register_api(hass, config_entry)
    config_entry.async_on_unload(config_entry.add_update_listener(_async_update_options))
    _LOGGER.info("YouTube Content Search services configured")
    return True


# Apply options without reloading playlists; related: config_flow.py.
async def _async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Apply updated credentials to subsequent service calls."""
    await async_setup_entry_credentials(hass, config_entry)


async def async_setup_entry_credentials(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update credentials without adding another options listener."""
    api_key = config_entry.options.get(CONF_API_KEY, config_entry.data.get(CONF_API_KEY))
    if not isinstance(api_key, str) or not api_key.strip():
        raise ConfigEntryError("YouTube API key is required")
    hass.data.setdefault(DOMAIN, {})[CONF_API_KEY] = api_key.strip()


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Keep existing data and options compatible with version 1 entries."""
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Remove credentials; registered actions remain available with explicit errors."""
    # Retain saved data while removing runtime states; related: playlist_store.py.
    playlists = hass.data.get(DOMAIN, {}).get(DATA_PLAYLIST_STORE)
    if playlists is not None:
        await playlists.async_clear_states()
    hass.data.pop(DOMAIN, None)
    return True


# Register actions once in async_setup; related: services.py and services.yaml.
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register actions independently of the config entry lifecycle."""
    hass.data.setdefault(DOMAIN, {})
    await async_setup_services(hass)
    return True
