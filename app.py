import streamlit as st # 建立網頁頁面用
from googleapiclient.discovery import build # Google 官方提供的 API 連線工具

# 讀取 API 金鑰
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


# 去 Youtube 抓資料
def get_yt_music(mood_query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    search_response = youtube.search().list(
        q=f"{mood_query} official music video", 
        part="snippet",
        type="video",
        maxResults=15,           # 稍微增加數量，確保過濾後還有足夠影片
        videoCategoryId="10"     # 注意：音樂類別代碼通常是 10
    ).execute()
    
    return search_response["items"]


# 網頁介面
st.set_page_config(page_title="心情音樂推薦", page_icon="🎧")
st.title("心情音樂推薦")
st.write("系統狀態：已連接至 YouTube Data API")

mood_options = {
    "🌟 充滿活力": "high energy workout rock",
    "🌙 深夜憂鬱": "sad emotional piano ballad",
    "📖 專注讀書": "lofi hip hop radio study chill",
    "🥳 快樂派對": "upbeat dance pop party",
    "☕ 輕音樂放鬆": "calm acoustic guitar instrumental"
}

selected_mood = st.selectbox("你現在的心情如何？", list(mood_options.keys()))
artist_input = st.text_input("你有想聽的歌手嗎？", placeholder="例如：Taylor Swift, Ava Max...")

if st.button("幫我挑選音樂"):
    with st.spinner("正在尋找該歌手的官方音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []

            if artist_input.strip():
                # 策略：只用歌手名字搜尋，不加心情關鍵字，避免干擾演算法
                # 我們搜尋「歌手名 + official」，這樣最容易抓到官方頻道
                search_keyword = f"{artist_input} official"
                st.write(f"正在搜尋「{artist_input}」的官方作品...")
                
                raw_songs = get_yt_music(search_keyword)
                
                # 方法 3：嚴格比對頻道名稱
                for song in raw_songs:
                    channel_name = song["snippet"]["channelTitle"].lower()
                    user_input_lower = artist_input.lower()
                    
                    # 只要頻道名字裡有歌手的名字，就認定是官方或相關頻道
                    if user_input_lower in channel_name:
                        final_songs.append(song)
                
                # 如果該歌手真的沒結果，才退而求其次用心情找
                if not final_songs:
                    st.info(f"在官方頻道中找不到相關內容，改為您推薦「{selected_mood}」的熱門歌曲。")
                    final_songs = get_yt_music(base_query)
            else:
                # 沒輸入歌手，直接用心情找
                final_songs = get_yt_music(base_query)

            # --- 顯示結果的邏輯 ---
            if final_songs:
                cols = st.columns(3)
                for idx, song in enumerate(final_songs[:12]):
                    with cols[idx % 3]:
                        title = song["snippet"]["title"]
                        video_id = song['id']['videoId']
                        channel = song["snippet"]["channelTitle"]
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                        st.video(video_url)
                        st.markdown(f"**[{title}]({video_url})**")
                        st.caption(f"🎤 頻道：{channel}")
                        st.write("---")
            else:
                st.warning("查無結果，請試著簡化歌手名稱。")

        except Exception as e:
            st.error(f"發生錯誤：{e}")