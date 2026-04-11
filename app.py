import os
import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

def get_yt_music(mood_query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    search_response = youtube.search().list(
        q=f"{mood_query} official music video",
        part='snippet',
        type='video',
        maxResults=6,
        videoCategoryId='10' 
    ).execute()
    
    return search_response['items']

st.set_page_config(page_title="心情音樂盒", page_icon="🎧")

st.title("🎧 我的專屬心情音樂盒")
st.write("目前狀態：**已連接至 YouTube Data API**")

mood_options = {
    "🌟 充滿活力 (Energetic)": "high energy workout rock",
    "🌙 深夜憂鬱 (Sad/Melancholy)": "sad emotional piano ballad",
    "📖 專注讀書 (Focus/Lofi)": "lofi hip hop radio study chill",
    "🥳 快樂派對 (Happy/Party)": "upbeat dance pop party",
    "☕ 輕音樂放鬆 (Relaxing)": "calm acoustic guitar instrumental"
}

selected_mood = st.selectbox("你現在的心情如何？", list(mood_options.keys()))

if st.button("幫我挑選音樂"):
    with st.spinner('正在為您尋找最適合的音樂...'):
        try:
            songs = get_yt_music(mood_options[selected_mood])
            
            cols = st.columns(2)
            for idx, song in enumerate(songs):
                with cols[idx % 2]:
                    title = song['snippet']['title']
                    video_id = song['id']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    thumbnail = song['snippet']['thumbnails']['high']['url']
                    
                    st.image(thumbnail, use_container_width=True)
                    st.markdown(f"**[{title}]({video_url})**")
                    st.video(video_url)
                    st.write("---")
        except Exception as e:
            st.error(f"糟糕，搜尋出錯了：{e}")
            st.info("請檢查您的 API Key 是否正確且已啟用 YouTube Data API v3。")