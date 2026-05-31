from googleapiclient.discovery import build
import streamlit as st

YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

def get_yt_music(query, duration="medium", use_music_category=True):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 30,
        "videoDuration": duration
    }
    if use_music_category:
        search_params["videoCategoryId"] = "10"
    
    try:
        search_response = youtube.search().list(**search_params).execute()
        return search_response.get("items", [])
    except Exception as e:
        st.error(f"YouTube API 錯誤: {e}")
        return []