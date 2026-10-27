# YouTube Content Search

[English](README.md) | [한국어](README.ko.md)

[Changelog](CHANGELOG.md)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![version](https://img.shields.io/badge/version-v1.1.0-blue.svg?style=for-the-badge)
[![kofi](https://img.shields.io/badge/Ko--fi-Support%20Me-F16061?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/plplaaa2)

Search and play YouTube videos through Home Assistant actions.
The sidebar panel and HTTP search endpoints are currently inactive.

## Installation and setup

### Automatic installation (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=plplaaa2&repository=https%3A%2F%2Fgithub.com%2Fplplaaa2%2Fyoutube_content_search&category=integration)

Click the badge above and install the integration.

### Manual installation

Copy only the `custom_components/youtube_content_search` folder to `/config/custom_components/youtube_content_search` in Home Assistant.

### Configure

1. Enable YouTube Data API v3 in Google Cloud and prepare an API key.
2. Set up Google Cast and/or Android TV Remote. Android TV app modes require an Android TV Remote `remote` entity.
3. Restart Home Assistant, then add YouTube Content Search from **Settings → Devices & services → Add integration**.
4. Enter the API key and playback mode in the integration configuration. Option changes apply to subsequent actions.

The key is stored in the Home Assistant config entry; this integration does not provide additional encryption. You do not need to put the actual key in automation YAML.

## Search and play

Call the action from **Developer tools → Actions**, an automation, or a script. It plays the first matching video; playlist search is not supported. Select official YouTube app to Cast fallback, SmartTube to Cast fallback, or Google Cast only in the integration options. App-link modes request Cast playback if the remote action returns an error.

Android TV app modes send a video deep link to an Android TV Remote `remote` entity and use `cast_entity_id` for the Google Cast `media_player` fallback. SmartTube mode uses its `vnd.youtube.launch` link. Deep-link handling can vary by device and app version.

```yaml
action: youtube_content_search.search_play
data:
  query: "IU live"
  entity_id: media_player.living_room_tv # use remote.living_room_tv for app-link mode
```

To play a specific video without searching, use `video` with a YouTube video URL or 11-character video ID instead of `query`. Provide exactly one of `query` or `video`.

```yaml
action: youtube_content_search.search_play
data:
  video: "https://youtu.be/dQw4w9WgXcQ"
  entity_id: media_player.living_room_tv # use remote.living_room_tv for app-link mode
```

## Connect the Assist tool

Install the updated integration and restart Home Assistant. You need an LLM conversation agent that supports tool calls.

1. In **Settings → Voice assistants**, expose both the Android TV Remote and Cast player to Assist.
2. In the conversation agent settings, select **YouTube Content Search** under **Tool providers** or **Control Home Assistant / LLM API**.
3. The tool is not added automatically to the built-in **Assist** API.
4. Ask the voice assistant using that agent, for example, “Play IU live on the living room TV.”

The tool is named `youtube_content_search__search_play`. It accepts either `query` (search terms) or `video` (a YouTube video URL or ID), plus `entity_id`. Specify only one of `query` and `video`.

Assist receives targets for the selected playback mode and checks integration ownership again before calling the action. App-link modes require both the Android TV Remote and Cast player.

A successful response means the playback request was sent; it does not confirm that video or audio actually started. API keys and raw backend errors are not sent to the LLM.

Settings names vary by Home Assistant version and conversation agent. The built-in conversation agent does not call this LLM tool. Windows mock tests cover provider setup and reload, API tool discovery, permissions, and error handling; actual Home Assistant listing and playback require separate verification.

If the provider is missing, check that the integration is installed and loaded after restarting Home Assistant, then reopen the conversation agent settings.

Official interface: [Home Assistant LLM API and tool contribution](https://developers.home-assistant.io/docs/core/llm/).

## Troubleshooting and removal

API errors and empty search results are reported as action errors. Check API usage and permissions in Google Cloud. API errors show the HTTP status and allowlisted reason codes; keys, request URLs, and raw response text are not displayed.

For example, `HTTP 400 (reason: invalidFilters)` indicates an invalid request filter, while `API_KEY_INVALID` points to the key. Check that the API is enabled for `SERVICE_DISABLED` and review quota usage for `quotaExceeded`. Unknown codes and non-JSON responses are shown as `reason: UNKNOWN`.

Restart Home Assistant after updating files. Removing the integration entry clears runtime credentials. To remove the code, uninstall it through HACS or delete the manual installation folder, then restart Home Assistant. Frontend files and the unconnected `options_flow.py` are retained; the active options flow is in `config_flow.py`.

## Development checks

On Windows, install `aiohttp` and `voluptuous` in Python, then run:

```powershell
python -B -m unittest discover -s tests -v
```

Tests mock Home Assistant interfaces. Actual Home Assistant configuration loading, API authentication, and TV playback require separate verification.

The HACS validation GitHub Action runs on pushes, pull requests, daily, and on manual dispatch. It validates this repository as an integration.

## Official references

- [Home Assistant manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant custom integration translations](https://developers.home-assistant.io/docs/internationalization/custom_integration/)
- [Google Cast YouTube playback](https://www.home-assistant.io/integrations/cast/#youtube)
- [YouTube video metadata](https://developers.google.com/youtube/v3/docs/videos/list)
- [HACS publishing requirements](https://www.hacs.xyz/docs/publish/integration/)
