# YouTube Content Search 1.2.0

Search YouTube videos with the YouTube Data API and request playback on Google Cast media players from Home Assistant actions or a compatible LLM conversation agent.

## Features

- Exposes a selectable **YouTube Content Search** LLM API for conversation agent tool providers.
- Uses the Google Cast integration criterion for both Assist discovery and action playback targets.
- Rejects non-Cast and unregistered media players before making a YouTube API request.
- Plays a selected YouTube video directly from a supported video URL or 11-character video ID.

## Requirements

- Home Assistant with a compatible LLM conversation agent for voice or chat tool use.
- A YouTube Data API v3 key configured in the integration.
- A Google Cast media player that supports the YouTube app.

After updating to 1.2.0 and restarting Home Assistant, select **YouTube Content Search** in the conversation agent's **Tool providers** or **LLM API** settings. See [README](README.md) for setup details.
