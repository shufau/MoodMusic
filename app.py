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
    with st.spinner("正在尋找最精準的音樂結果..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []

            if artist_input.strip():
                # 策略 A：指定歌手 + 頻道過濾
                st.write(f"🔍 正在篩選「{artist_input}」的官方頻道內容...")
                raw_songs = get_yt_music(f'intitle:"{artist_input}"') # 使用 intitle 強制匹配標題
                
                # 方法 3：比對 channelTitle
                for song in raw_songs:
                    channel_name = song["snippet"]["channelTitle"].lower()
                    target_artist = artist_input.lower()
                    
                    # 如果頻道名字包含歌手名，或是標題有官方字樣，才收入
                    if target_artist in channel_name:
                        final_songs.append(song)
                
                # 如果過濾完發現太少，補一點心情推薦
                if len(final_songs) < 2:
                    st.info(f"官方頻道結果較少，為您補充一些「{selected_mood}」的推薦。")
                    supplement_songs = get_yt_music(base_query)
                    final_songs.extend(supplement_songs[:6]) # 補 6 首
            else:
                # 策略 B：純心情推薦
                final_songs = get_yt_music(base_query)

            # 顯示結果
            if final_songs:
                # 這裡使用 list(set()) 的概念防止重複影片（依 videoId 判斷）
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    if s['id']['videoId'] not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(s['id']['videoId'])

                cols = st.columns(3)
                for idx, song in enumerate(unique_songs[:12]): # 最多顯示 12 首以免頁面過長
                    with cols[idx % 3]:
                        title = song["snippet"]["title"]
                        video_id = song['id']['videoId']
                        channel = song["snippet"]["channelTitle"] # 取得頻道名
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                        st.video(video_url)
                        # 在標題下方標註發布頻道，讓使用者知道是誰發的
                        st.markdown(f"**[{title}]({video_url})**")
                        st.caption(f"🎤 來源：{channel}")
                        st.write("---")
            else:
                st.warning("找不到相符的音樂，請換個歌手試試看！")
                    
        except Exception as e:
            st.error(f"詳細錯誤資訊：{e}")