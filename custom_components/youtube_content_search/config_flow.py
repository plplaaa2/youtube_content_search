import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY

# Config Flow: 최초 등록 시 API 키 입력
class YouTubeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        # 이미 엔트리가 있으면 추가 불가
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="YouTube Search", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    # 옵션 플로우 핸들러 연결
    @staticmethod
    def async_get_options_flow(config_entry):
        return YouTubeOptionsFlowHandler(config_entry)


# Options Flow: 재구성 시 API 키 변경 가능
class YouTubeOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(
                CONF_API_KEY,
                default=self._entry.data.get(CONF_API_KEY, "")
            ): str
        })
        return self.async_show_form(step_id="init", data_schema=schema)
