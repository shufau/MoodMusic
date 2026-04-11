import streamlit as st # 建立網頁頁面用
from googleapiclient.discovery import build # Google 官方提供的 API 連線工具

# 讀取 API 金鑰
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

# 去 Youtube 抓資料
def get_yt_music(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_response = youtube.search().list(
        q=f"{query}", # 這裡傳入組合好的純淨關鍵字
        part="snippet",
        type="video",
        maxResults=100,           # 增加搜尋筆數，因為後續會過濾，樣本多一點比較保險
        videoCategoryId="10"     # 強制鎖定音樂類別
    ).execute()
    return search_response["items"]

# 網頁介面
st.set_page_config(page_title="心情音樂推薦", page_icon="🎧")
st.title("心情音樂推薦")

mood_options = {
    "🌟 充滿活力": "high energy workout rock",
    "🌙 深夜憂鬱": "sad emotional piano ballad",
    "📖 專注讀書": "lofi hip hop radio study chill",
    "🥳 快樂派對": "upbeat dance pop party",
    "☕ 輕音樂放鬆": "calm acoustic guitar instrumental"
}

selected_mood = st.selectbox("你現在的心情如何？", list(mood_options.keys()))
artist_input = st.text_input("你有想聽的歌手嗎？", placeholder="例如：Taylor Swift, 周杰倫...")

if st.button("幫我挑選音樂"):
    with st.spinner("正在為您篩選精確的音樂結果..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            # --- 核心邏輯修改處 ---
            if artist_input.strip():
                # 1. 搜尋策略：只搜歌手名稱 + official，避免心情字眼干擾搜尋
                search_keyword = f"{artist_input} official music video"
                st.write(f"正在搜尋包含「{artist_input}」名稱的影片...")
                
                raw_results = get_yt_music(search_keyword)
                
                # 2. 標題過濾：檢查標題是否真的含有歌手名字
                for song in raw_results:
                    video_title = song["snippet"]["title"].lower()
                    search_name = artist_input.lower()
                    
                    if search_name in video_title:
                        final_songs.append(song)
                
                # 如果過濾後一首都沒有，自動切換回心情模式
                if not final_songs:
                    st.info(f"找不到標題含有「{artist_input}」的官方音樂，為您改為推薦「{selected_mood}」歌曲。")
                    final_songs = get_yt_music(base_query)
            else:
                # 沒輸歌手，直接跑心情搜尋
                final_songs = get_yt_music(base_query)

            # --- 顯示結果 ---
            if final_songs:
                cols = st.columns(3)
                for idx, song in enumerate(final_songs[:12]): # 最多顯示 12 個
                    with cols[idx % 3]:
                        title = song["snippet"]["title"]
                        video_id = song['id']['videoId']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        st.video(video_url)
                        st.markdown(f"**[{title}]({video_url})**")
                        st.write("---")
            else:
                st.warning("查無結果，請嘗試其他關鍵字。")
                    
        except Exception as e:
            st.error(f"發生錯誤：{e}")