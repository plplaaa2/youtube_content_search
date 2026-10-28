DOMAIN = "youtube_content_search"
CONF_API_KEY = "api_key"
CONF_PLAYBACK_MODE = "playback_mode"
PLAYBACK_MODE_CAST = "cast"
PLAYBACK_MODE_YOUTUBE_APP = "youtube_app_fallback"
PLAYBACK_MODE_SMARTTUBE = "smarttube_fallback"
PLAYBACK_MODE_CAST_FALLBACK = "cast_fallback"
PLAYBACK_MODE_APP_LINKS = (PLAYBACK_MODE_YOUTUBE_APP, PLAYBACK_MODE_SMARTTUBE)
DEFAULT_PLAYBACK_MODE = PLAYBACK_MODE_CAST_FALLBACK

# Panel (Sidebar Web UI) - 슬러그만 저장 (.html 포함 안 함)
PANEL_TITLE = "YouTube Content Search"
PANEL_ICON = "mdi:youtube-tv"
PANEL_URL = "youtube-content-search"
