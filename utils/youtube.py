from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

# 搜尋音樂
def search_music(query, limit=30):
    
    if not query or not query.strip():
        query = "2025 hit songs 流行熱門"
        
    try:

        songs = ytmusic.search(query, filter="songs", limit=limit)
        videos = ytmusic.search(query, filter="videos", limit=limit)
        
        combined_results = songs + videos

        if len(combined_results) < 10:
            combined_results += ytmusic.search(query, limit=limit)
            
        formatted_results = []
        seen_ids = set()
        
        for item in combined_results:
            vid = item.get("videoId")

            if vid and vid not in seen_ids:
                creators = item.get("artists") or item.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                
                formatted_results.append({
                    "video_id": vid,
                    "title": item["title"],
                    "artist": artist_name
                })
                seen_ids.add(vid)
                
                if len(formatted_results) >= limit:
                    break
                    
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []


# 根據給定的歌曲 ID，取得曲風相似的推薦歌單
def get_similar_music(video_id, limit=20):
    try:
        playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit)
        tracks = playlist.get("tracks", [])
        
        formatted_results = []
        for song in tracks[1:]:
            if song.get("videoId"):
                creators = song.get("artists") or song.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                formatted_results.append({
                    "video_id": song["videoId"],
                    "title": song["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"取得相似歌曲發生錯誤: {e}")
        return []