from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def search_music(query, limit=30):
    """終極貪婪搜尋：同時抓取歌曲與影片，並合併去重"""
    
    # 1. 終極防呆：避免空字串引發 HTTP 400 錯誤
    if not query or not query.strip():
        query = "2024 hit songs 流行熱門"
        
    try:
        # 2. 雙管齊下：同時抓取官方歌曲與官方 MV (保證數量絕對充足)
        songs = ytmusic.search(query, filter="songs", limit=limit)
        videos = ytmusic.search(query, filter="videos", limit=limit)
        
        combined_results = songs + videos
        
        # 3. 如果這樣還不夠，再補上全局搜尋
        if len(combined_results) < 10:
            combined_results += ytmusic.search(query, limit=limit)
            
        formatted_results = []
        seen_ids = set()
        
        for item in combined_results:
            vid = item.get("videoId")
            # 確保是可播放的影片，且沒有重複加入過
            if vid and vid not in seen_ids:
                creators = item.get("artists") or item.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                
                formatted_results.append({
                    "video_id": vid,
                    "title": item["title"],
                    "artist": artist_name
                })
                seen_ids.add(vid)
                
                # 達到我們需要的數量就收工
                if len(formatted_results) >= limit:
                    break
                    
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []

def get_similar_music(video_id, limit=20):
    """根據給定的歌曲 ID，取得曲風相似的推薦歌單"""
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