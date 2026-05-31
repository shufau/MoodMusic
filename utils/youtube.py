from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def search_music(query, limit=20):
    """用於有明確『歌手』或『歌名』的精確搜尋"""
    try:
        # 第一階段：嚴格過濾，只找官方「歌曲 (songs)」
        results = ytmusic.search(query, filter="songs", limit=limit)
        
        # 第二階段備案：如果找不到，放寬條件全局搜尋
        if not results:
            results = ytmusic.search(query, limit=limit)
            
        formatted_results = []
        for item in results:
            if item.get("videoId"):
                creators = item.get("artists") or item.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                formatted_results.append({
                    "video_id": item["videoId"],
                    "title": item["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []

def search_by_style(style_keyword, limit=30):
    """用於只有『風格』時，直接進行廣泛的單曲海選"""
    try:
        # 為了確保能搜到滿滿的歌，我們在關鍵字後面加上 "popular songs"，並進行全局搜尋
        query = f"{style_keyword} popular songs"
        results = ytmusic.search(query, limit=50) # 多抓一點來篩選
        
        formatted_results = []
        seen_ids = set() # 記錄已經加過的歌，避免重複
        
        for item in results:
            vid = item.get("videoId")
            # 只挑選帶有影片 ID 的結果 (過濾掉純文字的歌手頁面或專輯頁面)
            if vid and vid not in seen_ids:
                creators = item.get("artists") or item.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                
                formatted_results.append({
                    "video_id": vid,
                    "title": item["title"],
                    "artist": artist_name
                })
                seen_ids.add(vid)
                
                # 抓滿我們需要的數量就停止
                if len(formatted_results) >= limit:
                    break
                    
        return formatted_results
    except Exception as e:
        st.error(f"風格搜尋發生錯誤: {e}")
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