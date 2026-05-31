from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def search_music(query, limit=20):
    """有明確歌手或歌名時的精確搜尋（具備自動補貨機制）"""
    try:
        # 1. 第一波：抓官方純歌曲 (songs)
        songs_results = ytmusic.search(query, filter="songs", limit=limit)
        
        # 2. 第二波：同時抓官方 MV 與影片 (videos)，用來混音備用
        video_results = ytmusic.search(query, filter="videos", limit=limit)
        
        # 將兩波搜刮到的結果合併（此時裡面可能會有重複的歌或大量垃圾訊息）
        combined_results = songs_results + video_results
        
        # 3. 終極保險：如果中英混雜太嚴重導致前兩波加起來還少於 5 首，直接啟動大範圍全局搜尋
        if len(combined_results) < 5:
            combined_results = ytmusic.search(query, limit=limit * 2)
            
        # 進行嚴格的去重與格式化處理
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
                
                # 只要數量滿足使用者的限制，就立刻收工
                if len(formatted_results) >= limit:
                    break
                    
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []

def search_by_style(style_keyword, limit=30):
    """只有風格時的全局海選（雙重關鍵字掃描）"""
    try:
        # 同時用兩種關鍵字格式去撈，確保數量絕對充足
        res1 = ytmusic.search(f"{style_keyword} hot tracks", limit=30)
        res2 = ytmusic.search(style_keyword, limit=30)
        
        combined_results = res1 + res2
        
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