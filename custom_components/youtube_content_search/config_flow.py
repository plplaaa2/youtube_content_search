import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_API_KEY

# Config Flow: 최초 등록 시 API 키 입력
class YouTubeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        # 이미 엔트리가 있으면 추가 불가
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Normalize required credentials; related: __init__.py and translations/.
        errors = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            if api_key:
                return self.async_create_entry(title="YouTube Search", data={CONF_API_KEY: api_key})
            errors["base"] = "api_key_required"

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # 옵션 플로우 핸들러 연결
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return YouTubeOptionsFlowHandler(config_entry)


# Options Flow: 재구성 시 API 키 변경 가능
class YouTubeOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._entry = entry

    async def async_step_init(self, user_input=None):
        # Apply options through the entry listener; related: __init__.py.
        errors = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            if api_key:
                return self.async_create_entry(title="", data={CONF_API_KEY: api_key})
            errors["base"] = "api_key_required"

        schema = vol.Schema({
            vol.Required(
                CONF_API_KEY,
                default=self._entry.options.get(CONF_API_KEY, self._entry.data.get(CONF_API_KEY, ""))
            ): str
        })
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
