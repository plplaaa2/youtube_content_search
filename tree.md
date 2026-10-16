# Project structure

HA service integration with Assist LLM tools. Frontend and legacy backup assets are retained but inactive.

```text
LICENSE
README.md
caution.jsonl
changelog.jsonl
custom_components/youtube_content_search/__init__.py
custom_components/youtube_content_search/config_flow.py
custom_components/youtube_content_search/const.py
custom_components/youtube_content_search/llm.py
custom_components/youtube_content_search/frontend/panel.html
custom_components/youtube_content_search/frontend/panel.js
custom_components/youtube_content_search/frontend/styles.css
custom_components/youtube_content_search/manifest.json
custom_components/youtube_content_search/options_flow.py
custom_components/youtube_content_search/playlist_store.py
custom_components/youtube_content_search/services.py
custom_components/youtube_content_search/services.yaml
custom_components/youtube_content_search/translations/en.json
custom_components/youtube_content_search/translations/ko.json
hacs.json
icon.png
info.md
logo.png
tests/test_service_only.py
tree.md
validate_syntax.py
youtube_content_search_backup/__init__.py
youtube_content_search_backup/config_flow.py
youtube_content_search_backup/const.py
youtube_content_search_backup/manifest.json
youtube_content_search_backup/services.py
youtube_content_search_backup/services.yaml
```

servers/ contains only Git metadata and is outside the integration runtime.
