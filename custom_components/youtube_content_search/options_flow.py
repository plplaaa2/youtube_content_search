"""YouTube Content Search Options Flow - Secure API key management."""

import logging
from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


class YouTubeContentSearchOptionsFlow:
    """Handle options flow for YouTube Content Search integration."""

    VERSION = 1
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.store_key = f"{DOMAIN}_options"

    @property
    def store(self) -> Store:
        return Store(self.store_key, self.VERSION)

    async def async_show_form(self) -> Dict[str, Any]:
        """Create and show the options form for API key input."""
        return {
            "title": "YouTube Content Search Settings",
            "form_step_id": "api_key",
            "data_schema": None,  # Custom schema in callback
            "description_placeholders": {},
        }

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the API key configuration step."""
        
        if not user_input or CONF_API_KEY not in user_input:
            return self.async_show_form()

        api_key_value = user_input.get(CONF_API_KEY)

        # Validate API key is not empty
        if not api_key_value.strip():
            _LOGGER.error("YouTube API Key cannot be empty")
            return {
                "title": "YouTube Content Search",
                "form_step_id": "api_key",
                "errors": {"base": "api_key_required"},
                "data_schema": None,
                "description_placeholders": {},
            }

        try:
            # Save to secure storage helper (Store pattern)
            await self.store.async_save({CONF_API_KEY: api_key_value})
            
            # Also update hass.data for immediate use by services
            if DOMAIN not in self.hass.data:
                self.hass.data[DOMAIN] = {}
            self.hass.data[DOMAIN][CONF_API_KEY] = api_key_value

        except Exception as err:
            _LOGGER.error("Error saving YouTube API Key: %s", err, exc_info=True)
            return {
                "title": "YouTube Content Search",
                "form_step_id": "api_key",
                "errors": {"base": "save_error"},
                "data_schema": None,
                "description_placeholders": {},
            }

        return self.async_create_entry(
            title="YouTube Content Search",
            data={CONF_API_KEY: api_key_value}
        )