import streamlit as st # 建立網頁頁面用
from googleapiclient.discovery import build # Google 官方提供的 API 連線工具

# 讀取 API 金鑰
# 雲端部署 -> 找設定的環境變數
# 本地部屬 -> 找 .streamlit/secrets.toml
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


# 去 Youtube 抓資料
def get_yt_music(mood_query):
    # 建立 Youtube API 服務物件
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    # 呼叫 Youtube 的搜尋功能
    search_response = youtube.search().list(
        q=f"{mood_query} official music video", # 關鍵字 + 官方 MV
        part="snippet",         # 只回傳基本資訊
        type="video",           # 只要影片
        maxResults=16,           # 抓取筆數
        videoCategoryId="10"    # 類別代碼（10 為音樂）
    ).execute()
    
    # 回傳搜尋到的影片清單
    return search_response["items"]


# 網頁介面
st.set_page_config(page_title="心情音樂推薦", page_icon="🎧")
st.title("心情音樂推薦")
st.write("系統狀態：已連接至 YouTube Data API")

# 心情對照表（下拉選項: 搜尋關鍵字）
mood_options = {
    "🌟 充滿活力": "high energy workout rock",
    "🌙 深夜憂鬱": "sad emotional piano ballad",
    "📖 專注讀書": "lofi hip hop radio study chill",
    "🥳 快樂派對": "upbeat dance pop party",
    "☕ 輕音樂放鬆": "calm acoustic guitar instrumental"
}

# 下拉式選單
selected_mood = st.selectbox("你現在的心情如何？", list(mood_options.keys()))

# 指定歌手
artist_input = st.text_input("你有想聽的歌手嗎？(留空則由系統隨機推薦)", placeholder="例如：Taylor Swift, Ava Max, ...")

# 按鈕觸發
if st.button("幫我挑選音樂"):
    # 工作中畫面
    with st.spinner("正在為您尋找最適合的音樂..."):
        try:
            # 嘗試選歌
            base_query = mood_options[selected_mood]
            if artist_input.strip():
                final_query = f"{artist_input} {base_query}"
                st.write(f"正在搜尋「{artist_input}」的相關音樂...")
            else:
                final_query = base_query
            songs = get_yt_music(mood_options[final_query])

            # 建立兩欄式佈局
            cols = st.columns(3)
            for idx, song in enumerate(songs):
                with cols[idx % 3]:
                    title = song["snippet"]["title"]    # 取得影片標題
                    video_id = song['id']['videoId']    # 取得影片 ID
                    video_url = f"https://www.youtube.com/watch?v={video_id}"   # 組合網址

                    st.video(video_url) # 嵌入式播放器
                    st.markdown(f"**[{title}]({video_url})**")  # 帶連結的標題
                    st.write("---")
                    
        except Exception as e:
            st.error(f"詳細錯誤資訊：{e}") # 這樣會顯示具體的錯誤原因，例如 403 Forbidden 或 400 Bad Request
            st.info("關鍵字：" + final_query)