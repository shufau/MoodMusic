import streamlit as st
from googleapiclient.discovery import build

# 讀取 API 金鑰
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


# 去 Youtube 抓資料
def get_yt_music(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_response = youtube.search().list(
        q=f"{query}", # 搜尋關鍵字
        part="snippet", # 只回傳基本資訊
        type="video", # 只回傳影片類型
        maxResults=1000, # 抓取筆數
        videoCategoryId="10" # 類別代碼（10 為音樂）
    ).execute()
    
    # 回傳搜尋到的影片清單
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
artist_input = st.text_input("你有想聽的歌手嗎？", placeholder="例如：Taylor Swift, Katy Perry, Juicy J, ...")

# 推薦區域
with st.sidebar:
    st.header("站長私心推薦")
    st.write("如果你不知道聽什麼，試試這些：")
    
    # 推薦歌曲 1
    st.subheader("Sign of the Times")
    st.video("https://youtu.be/qN4ooNx77u0?si=Pz0B0Z58xbeQ3k6R")
    st.caption("最近一直循環播放")
    
    st.write("---")
    
    # 推薦歌曲 2
    st.subheader("Unconditionally")
    st.video("https://youtu.be/XjwZAa2EjKA?si=DCwKjgvpzWYQJ99R")
    st.caption("小時候常聽的歌")


# 按鈕觸發
if st.button("幫我挑選音樂"):
    with st.spinner("正在挑選最適合的音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            # 定義官方關鍵字標示
            official_keywords = ["official", "mv", "music video", "original", "vocal", "lyric"]

            # 1. 決定搜尋關鍵字並執行初次搜尋
            if artist_input.strip():
                # 使用「歌手名 + 心情」搜尋
                search_keyword = f"{artist_input} {base_query}"
                st.write(f"🔍 正在搜尋「{artist_input}」的「{selected_mood}」相關作品...")
            else:
                # 沒輸入歌手，純心情搜尋
                search_keyword = base_query
                st.write(f"🔍 正在搜尋「{selected_mood}」的熱門音樂...")

            raw_results = get_yt_music(search_keyword)

            # 2. 標題過濾邏輯
            for song in raw_results:
                title_lower = song["snippet"]["title"].lower()
                
                # 檢查官方標示
                is_official = any(k in title_lower for k in official_keywords)
                
                # 檢查歌手名稱 (如果有指定)
                has_artist = True
                if artist_input.strip():
                    has_artist = artist_input.lower() in title_lower
                
                # 符合條件才加入
                if is_official and has_artist:
                    final_songs.append(song)

            # 3. 補足機制 (當結果低於 12 首時啟動) 
            if len(final_songs) < 1:
                if artist_input.strip():
                    # 有指定歌手 -> 補足該歌手的其他官方作品 (不限心情)
                    st.info(f"符合當前心情的作品較少，系統將為您增加「{artist_input}」的其他熱門作品。")
                    backup_keyword = f"{artist_input} official music video"
                else:
                    # 沒指定歌手 -> 補足該心情的其他官方作品 (擴大搜尋範圍)
                    st.info(f"正在為您搜尋更多「{selected_mood}」相關的官方推薦歌曲...")
                    backup_keyword = f"music official"
                
                backup_results = get_yt_music(backup_keyword)
                
                for song in backup_results:
                    title_lower = song["snippet"]["title"].lower()
                    # 補足時一樣要檢查官方標示
                    is_official = any(k in title_lower for k in official_keywords)
                    
                    has_artist = True
                    if artist_input.strip():
                        has_artist = artist_input.lower() in title_lower
                    
                    # 確保符合官方標示、符合歌手(若有)且不重複
                    if is_official and has_artist and song not in final_songs:
                        final_songs.append(song)

            # 4. 顯示結果 (2 欄式佈局，最多顯示 48 個)
            if final_songs:
                # 確保不重複（根據 videoId）
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    vid = s['id']['videoId']
                    if vid not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(vid)

                cols = st.columns(2)
                for idx, song in enumerate(unique_songs[:48]):
                    with cols[idx % 2]:
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