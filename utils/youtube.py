from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def get_best_video(query):
    """給定精確歌名，回傳最適合播放的 YouTube Video ID"""
    try:
        # filter="songs" 確保我們只會拿到官方正版音檔，不會拿到奇怪的翻唱
        results = ytmusic.search(query, filter="songs", limit=1)
        if results and results[0].get("videoId"):
            return results[0]["videoId"]
        return None
    except Exception as e:
        st.error(f"YouTube 搜尋發生錯誤: {e}")
        return None