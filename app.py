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
        maxResults=160, # 抓取筆數
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

if st.button("幫我挑選音樂"):
    with st.spinner("正在為您挑選最適合的音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            if artist_input.strip():
                # 1. 搜尋策略：將「歌手名」+「心情關鍵字」結合搜尋
                # 這樣 YouTube 會優先回傳該歌手符合該心情的影片
                search_keyword = f"{artist_input} {base_query} official"
                st.write(f"🔍 正在搜尋「{artist_input}」的「{selected_mood}」相關音樂...")
                
                raw_results = get_yt_music(search_keyword)
                
                # 2. 標題過濾：檢查標題是否含有歌手名字
                search_name = artist_input.lower()
                for song in raw_results:
                    video_title = song["snippet"]["title"].lower()
                    
                    # 只有標題包含歌手名字的才放進清單
                    if search_name in video_title:
                        final_songs.append(song)
                
                # 3. 備案機制：如果同時滿足「歌手+心情」的標題太少（少於 4 首）
                # 則改為只搜尋該歌手的「官方音樂」，不限心情，增加結果數量
                if len(final_songs) < 4:
                    st.info(f"符合當前心情的作品較少，改為您顯示「{artist_input}」的其他熱門作品。")
                    backup_results = get_yt_music(f"{artist_input} official music video")
                    for song in backup_results:
                        video_title = song["snippet"]["title"].lower()
                        # 同樣要檢查標題
                        if search_name in video_title and song not in final_songs:
                            final_songs.append(song)
                            
                # 4. 極限備案：如果還是找不到該歌手，最後才切換回純心情推薦
                if not final_songs:
                    st.warning(f"找不到標題含有「{artist_input}」的音樂，改為您推薦熱門的「{selected_mood}」歌曲。")
                    final_songs = get_yt_music(base_query)
            else:
                # 沒輸歌手，直接跑心情搜尋
                final_songs = get_yt_music(base_query)

            # --- 顯示結果 (維持原樣) ---
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
                # 最多顯示 48 個
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