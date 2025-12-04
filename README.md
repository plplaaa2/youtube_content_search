# Youtube Search & Play

This custom Home Assistant integration allows you to search for YouTube videos or playlists and cast them directly to supported media players (Nest Hub, Chromecast, smart TVs with Cast support).

#✨ Features
- Search YouTube by keyword using the YouTube Data API
- Automatically detect whether the result is a video or playlist
- Cast content to your chosen media player using the proper JSON payload
- Works seamlessly with Home Assistant scripts and automations

#🔧 Requirements
- A valid YouTube Data API key
- A Cast‑enabled device (e.g., Nest Hub, Chromecast, Cast‑enabled TV)

#🚀 Usage
- Install the integration under custom_components/youtube_content_search
- Configure your API key in Home Assistant
- Call the service youtube_content_search.search_play with:
- query: search keyword (required)
- entity_id: target media player (required)
