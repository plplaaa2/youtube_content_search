
# YouTube Content Search

[English](README.md) | [한국어](README.ko.md)

[Changelog](CHANGELOG.md)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-v1.2.0-blue.svg?style=for-the-badge)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20Me-F16061?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/plplaaa2)

Search for YouTube videos and play them on your TV through Home Assistant.
The integration also provides an LLM tool for voice control through compatible
Home Assistant conversation agents.

## Features

- **YouTube search and playback** — Search by keywords and play the first matching video.
- **Direct playback** — Play a video by URL or video ID, or start a playlist.
- **Multiple playback modes** — Use the official YouTube app, SmartTube, or Google Cast.
- **Voice control** — Expose the playback tool to a compatible LLM conversation agent.
- **Configurable playback** — Select the playback mode and related options in the integration configuration.

The sidebar panel and HTTP search endpoints are currently inactive.

## Requirements

- Home Assistant
- A YouTube Data API v3 API key
- A compatible playback target:
  - **Official YouTube app / SmartTube:** Android TV Remote and Google Cast integrations
  - **Google Cast only:** A Google Cast `media_player`
- For voice control: a conversation agent that supports LLM tool calls

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=https%3A%2F%2Fgithub.com%2Fplplaaa2%2Fyoutube_content_search&owner=plplaaa2&category=integration)
Click the badge to open HACS and install the integration.

### Manual installation

Copy the `custom_components/youtube_content_search` folder to:

`/config/custom_components/youtube_content_search`

### Initial setup

1. Enable **YouTube Data API v3** in Google Cloud and create an API key.
2. Set up the required Google Cast and/or Android TV Remote integrations.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **YouTube Content Search**, then enter your API key and playback mode.

Configuration changes apply to subsequent actions.

## Playback modes

| Mode | Playback method | Required entities |
| --- | --- | --- |
| Official YouTube app → Cast fallback | Opens the video in the TV's YouTube app; attempts Cast if the remote action returns an error | Android TV Remote `remote` + Cast `media_player` |
| SmartTube → Cast fallback | Opens the video through SmartTube's `vnd.youtube.launch` link; attempts Cast if the remote action returns an error | Android TV Remote `remote` + Cast `media_player` |
| Google Cast only | Sends the video directly to a Cast player | Cast `media_player` |

For app-link modes, install the required app on the TV. For SmartTube, set it as the default handler for YouTube links if Android TV asks.

A fallback is attempted when the remote action returns an error. It cannot detect every case where an app silently fails to open. Deep-link behavior may vary by device and app version.

## Usage

Call `youtube_content_search.search_play` from **Developer tools → Actions**, an automation, or a script.

### Search and play

```yaml
action: youtube_content_search.search_play
data:
  query: "IU live"
  entity_id: remote.living_room_tv
```

Use the appropriate `entity_id` for your selected playback mode:

- App-link modes: Android TV Remote `remote` entity
- Google Cast only: Cast `media_player` entity

### Play a video directly

Use `video` instead of `query` to provide a YouTube URL, an 11-character video ID, or a playlist URL.

```yaml
action: youtube_content_search.search_play
data:
  video: "https://youtu.be/dQw4w9WgXcQ"
  entity_id: remote.living_room_tv
```

For playlists, the integration resolves the first playable video and passes the playlist ID to YouTube so playback can continue through the list. Playlist lookup requires the YouTube Data API; private playlists may not be accessible with an API key alone.

Specify exactly one of `query` and `video`.

## Voice control with Assist

The integration exposes an LLM tool named:

`youtube_content_search__search_play`

It accepts `query` or `video`, plus `entity_id`.

### Setup

1. Install or update the integration and restart Home Assistant.
2. In **Settings → Voice assistants**, expose the required Android TV Remote and/or Cast player entities to Assist.
3. Open your conversation agent's settings.
4. Select **YouTube Content Search** under **Tool providers** or **Control Home Assistant / LLM API**, depending on your Home Assistant version and agent.
5. Use that conversation agent to issue a voice command, such as:

   "Play IU live on the living room TV."

The tool is not automatically added to the built-in Assist API. The built-in conversation agent does not call this LLM tool; a compatible agent with tool-calling support is required.

The tool validates target entities against the selected playback mode and checks integration ownership before executing the action. App-link modes require both the Android TV Remote and Cast player.

A successful response means the playback request was sent. It does not confirm that video or audio actually started. API keys and raw backend errors are not sent to the LLM.

If the provider is missing, verify that the integration loaded successfully after restarting Home Assistant, then reopen the conversation agent settings.

## Troubleshooting

### Search errors or no results

- Check that YouTube Data API v3 is enabled in Google Cloud.
- Verify the API key and API restrictions.
- Check API quota usage.

API errors and empty search results are reported as action errors. Error messages include the HTTP status and allowlisted reason codes, without exposing the API key, request URLs, or raw response text.

Examples:

- `SERVICE_DISABLED` — Check that the API is enabled.
- `API_KEY_INVALID` — Check the API key.
- `quotaExceeded` — Check API quota usage.
- `invalidFilters` — Check the request filters.

Unknown error codes and non-JSON responses are reported as `reason: UNKNOWN`.

### Playback does not start

- Confirm that the selected playback mode matches the configured entities.
- For app-link modes, verify Android TV Remote connectivity and that the target app is installed.
- For fallback playback, verify that the Google Cast player is available.
- Remember that a successful action response does not guarantee actual playback.

### Updating or removing the integration

Restart Home Assistant after updating the integration files.

To remove the integration, delete its entry from **Settings → Devices & services**. Removing the entry clears runtime credentials. Then uninstall it through HACS or delete the manual installation folder and restart Home Assistant.

## Security and privacy

The API key is stored in the Home Assistant config entry. This integration does not provide additional encryption, so protect your Home Assistant configuration and backups appropriately.

You do not need to include the actual API key in automation YAML.

## Development

The test suite uses mocked Home Assistant interfaces. It covers provider setup and reload, API tool discovery, permissions, and error handling. Actual Home Assistant loading, API authentication, and TV playback require separate verification.

On Windows, install the Python dependencies `aiohttp` and `voluptuous`, then run:

```powershell
python -B -m unittest discover -s tests -v
```

The HACS validation GitHub Action runs on pushes, pull requests, daily, and manual dispatch.

## Official references

- [Home Assistant LLM API and tool contribution](https://developers.home-assistant.io/docs/core/llm/)
- [Home Assistant integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant custom integration translations](https://developers.home-assistant.io/docs/internationalization/custom_integration/)
- [Google Cast YouTube playback](https://www.home-assistant.io/integrations/cast/#youtube)
- [YouTube video metadata API](https://developers.google.com/youtube/v3/docs/videos/list)
- [HACS publishing requirements](https://www.hacs.xyz/docs/publish/integration/)
