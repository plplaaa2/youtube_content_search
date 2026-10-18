# YouTube Content Search

[English](README.md) | [한국어](README.ko.md)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![version](https://img.shields.io/badge/version-v1.1.0-blue.svg?style=for-the-badge)
[![kofi](https://img.shields.io/badge/Ko--fi-Support%20Me-F16061?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/plplaaa2)

Search YouTube videos and request playback on Google Cast devices through Home Assistant actions.
The sidebar panel and HTTP search endpoints are currently inactive.

## Installation and setup

### Automatic installation (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=plplaaa2&repository=https%3A%2F%2Fgithub.com%2Fplplaaa2%2Fyoutube_content_search&category=integration)

Click the badge above and install the integration.

### Manual installation

Copy only the `custom_components/youtube_content_search` folder to `/config/custom_components/youtube_content_search` in Home Assistant.

### Configure

1. Enable YouTube Data API v3 in Google Cloud and prepare an API key.
2. Set up the Google Cast integration and identify the target `media_player` entity.
3. Restart Home Assistant, then add YouTube Content Search from **Settings → Devices & services → Add integration**.
4. Enter the API key in the integration configuration. Option changes apply to subsequent actions.

The key is stored in the Home Assistant config entry; this integration does not provide additional encryption. You do not need to put the actual key in automation YAML.

## Search and play

Call the action from **Developer tools → Actions**, an automation, or a script. It plays the first matching video; playlist search is not supported. Playback requires a Google Cast device that supports the YouTube app.

The action's device selector lists only `media_player` entities from the Google Cast integration. YAML targets are also checked before searching: entities without a registered `cast` platform are rejected. Remove the legacy `playback_mode` field from existing automations if you added it.

```yaml
action: youtube_content_search.search_play
data:
  query: "IU live"
  entity_id: media_player.living_room_tv
```

To play a specific video without searching, use `video` with a YouTube video URL or 11-character video ID instead of `query`. Provide exactly one of `query` or `video`.

```yaml
action: youtube_content_search.search_play
data:
  video: "https://youtu.be/dQw4w9WgXcQ"
  entity_id: media_player.living_room_tv
```

## Connect the Assist tool

Install the updated integration and restart Home Assistant. You need an LLM conversation agent that supports tool calls.

1. In **Settings → Voice assistants**, expose the target `media_player` to Assist.
2. In the conversation agent settings, select **YouTube Content Search** from **Tool providers** or **Control Home Assistant / LLM API**. The integration registers a separate LLM API when it loads.
3. If the agent supports multiple APIs, you may also select the built-in **Assist** API. YouTube tools are available only through **YouTube Content Search** and are not added to the built-in Assist API.
4. Ask the voice assistant using that agent, for example, “Play IU live on the living room TV.”

The tool is named `youtube_content_search__search_play`. It accepts either `query` (search terms) or `video` (a YouTube video URL or ID), plus `entity_id`. Specify only one of `query` and `video`.

Assist receives Google Cast media players using the same Cast integration criterion as the action selector, and the integration checks Cast ownership again before calling the action. The agent should ask when the requested player is ambiguous. The target must support the YouTube app.

A successful response means the playback request was sent; it does not confirm that video or audio actually started. Saving and deleting local playlists are not available as Assist tools. API keys and raw backend errors are not sent to the LLM.

Settings names vary by Home Assistant version and conversation agent. The built-in conversation agent does not call this LLM tool. Windows mock tests cover provider setup and reload, API tool discovery, permissions, and error handling; actual Home Assistant listing and playback require separate verification.

If the provider is missing, check that version `1.1.0` is installed, the integration loaded after restarting Home Assistant, and reopen the conversation agent settings. This version includes a standalone YouTube provider, Cast device restrictions, Assist integration, and direct playback from YouTube URLs or video IDs.

Official interface: [Home Assistant LLM API and tool contribution](https://developers.home-assistant.io/docs/core/llm/).

## Home Assistant local playlists

Playlists are stored in Home Assistant and do not modify your YouTube account. Video metadata is saved locally and restored after Home Assistant restarts or the integration reloads. There is no action to play an entire playlist. Playlist names are normalized for entity IDs, and duplicate videos are merged.

The storage file is `.storage/youtube_content_search.playlists` in the Home Assistant config directory. Additions and deletions are reflected in Home Assistant only after storage succeeds; deleted playlists stay deleted after a restart. Include this file in backups and do not edit it directly. The file is retained if you remove the integration entry, and playlists are restored when you configure it again.

If legacy temporary playlist states exist and there is no storage file, the first initialization imports them. Temporary states already lost after a Home Assistant restart cannot be recovered by updating the integration. A playlist management UI is not currently provided; use the actions and **Developer tools → States**.

```yaml
action: youtube_content_search.playlist_save
data:
  playlist_id: "my_music"
  video_ids:
    - "dQw4w9WgXcQ"
    - "jNQXAC9IVRw"
```

`video_ids` accepts a YAML list, comma-separated string, or JSON array string. To inspect a playlist, open `youtube_content_search._playlist_my_music` in **Developer tools → States** and check its `data` attribute.

```yaml
action: youtube_content_search.playlist_delete
data:
  id: "my_music"
```

## Troubleshooting and removal

API errors and empty search results are reported as action errors. Check API usage and permissions in Google Cloud. API errors show the HTTP status and allowlisted reason codes; keys, request URLs, and raw response text are not displayed.

For example, `HTTP 400 (reason: invalidFilters)` indicates an invalid request filter, while `API_KEY_INVALID` points to the key. Check that the API is enabled for `SERVICE_DISABLED` and review quota usage for `quotaExceeded`. Unknown codes and non-JSON responses are shown as `reason: UNKNOWN`.

Restart Home Assistant after updating files. Removing the integration entry clears runtime credentials. To remove the code, uninstall it through HACS or delete the manual installation folder, then restart Home Assistant. Frontend files and the unconnected `options_flow.py` are retained; the active options flow is in `config_flow.py`.

## Development checks

On Windows, install `aiohttp` and `voluptuous` in Python, then run:

```powershell
python -B -m unittest discover -s tests -v
```

Tests mock Home Assistant interfaces and use temporary files to verify playlist restoration. Actual Home Assistant Store behavior, configuration loading, API authentication, and Cast playback require separate verification.

## Official references

- [Home Assistant manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant custom integration translations](https://developers.home-assistant.io/docs/internationalization/custom_integration/)
- [Google Cast YouTube playback](https://www.home-assistant.io/integrations/cast/#youtube)
- [YouTube video metadata](https://developers.google.com/youtube/v3/docs/videos/list)
- [HACS publishing requirements](https://www.hacs.xyz/docs/publish/integration/)
