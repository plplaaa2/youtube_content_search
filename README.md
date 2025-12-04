# Youtube Search & Play

This custom Home Assistant integration allows you to search for YouTube videos or playlists and cast them directly to supported media players (Nest Hub, Chromecast, smart TVs with Cast support).

# Features
 - Search YouTube by keyword using the YouTube Data API
 - Automatically detect whether the result is a video or playlist
 - Cast content to your chosen media player using the proper JSON payload
 - Works seamlessly with Home Assistant scripts and automations

# Requirements
 - A valid YouTube Data API key
 - A Cast‑enabled device (e.g., Nest Hub, Chromecast, Cast‑enabled TV)

# Usage
 - Install the integration under custom_components/youtube_content_search
  <img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/27542206-8f3a-40ca-bdaf-778278df8aed" />
  
 - Configure your API key in Home Assistant
   
 <img width="378" height="233" alt="image" src="https://github.com/user-attachments/assets/7a456180-f1ca-4fac-8457-22aec0756760" />

 - Call the action youtube_content_search.search_play with:
  
 - query: search keyword (required)
 - entity_id: target media player (required)

