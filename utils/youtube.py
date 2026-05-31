from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def search_music(query, limit=30):
    """終極貪婪搜尋：同時抓取歌曲與影片，並合併去重"""
    
    if not query or not query.strip():
        query = "2024 hit songs 流行熱門"
        
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

def get_similar_music(video_id, limit=20):
    """
    強固型相似歌曲搜尋 (具備自動備援機制)
    策略一：嘗試抓取官方相似電台
    策略二：若電台失效，自動反查原唱歌手並搜尋其熱門歌曲
    """
    try:
        # 🚀 策略一：嘗試使用官方的「專屬電台 (Watch Playlist)」
        playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit)
        
        # 加上型態檢查，防止 NoneType 報錯
        if playlist and isinstance(playlist, dict):
            tracks = playlist.get("tracks", [])
            if len(tracks) > 1:
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
                if formatted_results:
                    return formatted_results
    except Exception as e:
        print(f"策略一 (電台) 遭阻擋或失效: {e}，準備啟動備援機制...")

    # ========================================================
    # 🚀 策略二：備援機制 (Fallback) - 抓取原唱歌手的其他熱門歌曲
    # ========================================================
    try:
        print("啟動策略二：反查歌手並進行關聯搜尋...")
        song_info = ytmusic.get_song(video_id)
        
        if song_info and "videoDetails" in song_info:
            author = song_info["videoDetails"].get("author", "")
            
            if author:
                fallback_query = f"{author} hit songs 音樂"
                fallback_results = search_music(fallback_query, limit=limit)
                
                # 過濾掉原本的那首歌
                filtered_fallback = [song for song in fallback_results if song["video_id"] != video_id]
                
                if filtered_fallback:
                    return filtered_fallback
    except Exception as e:
        print(f"策略二 (備援搜尋) 也失敗: {e}")
        
    return []