from ytmusicapi import YTMusic
import streamlit as st

# 初始化 ytmusic (完全免費，不需要 API key！)
ytmusic = YTMusic()

def search_music(query, limit=20):
    """搜尋 YouTube Music 上的官方歌曲"""
    try:
        # filter="songs" 會自動過濾掉翻唱、Podcast、純影片
        results = ytmusic.search(query, filter="songs", limit=limit)
        
        formatted_results = []
        for song in results:
            if song.get("videoId"):
                artist_name = ", ".join([a["name"] for a in song.get("artists", [])])
                formatted_results.append({
                    "video_id": song["videoId"],
                    "title": song["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []

def get_similar_music(video_id, limit=20):
    """根據給定的歌曲 ID，取得曲風相似的推薦歌單"""
    try:
        # 呼叫 YouTube Music 的「電台」功能
        playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit)
        tracks = playlist.get("tracks", [])
        
        formatted_results = []
        # 從第 1 首開始抓 (略過第 0 首，因為第 0 首是原本查詢的那首歌)
        for song in tracks[1:]:
            if song.get("videoId"):
                artist_name = ", ".join([a["name"] for a in song.get("artists", [])])
                formatted_results.append({
                    "video_id": song["videoId"],
                    "title": song["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"取得相似歌曲發生錯誤: {e}")
        return []