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
        maxResults=50, # 抓取筆數
        videoCategoryId="10", # 類別代碼（10 為音樂）
        videoDuration="medium"
    ).execute()
    
    # 回傳搜尋到的影片清單
    return search_response["items"]


# 網頁介面
st.set_page_config(page_title="音樂推薦系統", page_icon="🎧")
st.title("音樂推薦系統")

mood_options = {
    "✨ 活力滿點": "upbeat pop anthem",
    "🌙 深夜憂鬱": "ballad song",
    "☕ 輕午茶放鬆": "acoustic folk",
    "🔥 燃燒鬥志": "energetic rock",
    "🌌 靜謐沉澱": "minimalist piano",
    "💃 快樂搖擺": "funky dance pop",
    "🎷 復古情懷": "jazz soul audio",
    "🎤 情感爆發": "power ballad vocal"
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
            # 取得優化後的氛圍關鍵字
            base_query = mood_options[selected_mood]
            final_songs = []
            
            # 1. 定義過濾標準
            # 官方標示關鍵字
            official_keywords = ["official", "mv", "music video", "original", "vocal", "lyric", "audio"]
            # 強制排除黑名單 (封殺合輯、廣播、長時間影片)
            blacklist = ["mix", "playlist", "24/7", "lofi", "meditation", "relaxing", "hours", "nonstop"]

            # 2. 決定搜尋關鍵字並執行搜尋
            if artist_input.strip():
                # 指定歌手時，關鍵字盡量精簡以提升命中率
                search_keyword = f"{artist_input} {base_query}"
                st.write(f"🔍 正在搜尋「{artist_input}」的氛圍作品...")
            else:
                # 純心情搜尋時，增加 music 以對齊官方頻道標籤
                search_keyword = f"{base_query} music"
                st.write(f"🔍 正在搜尋「{selected_mood}」的推薦音樂...")

            raw_results = get_yt_music(search_keyword)

            # 3. 核心過濾邏輯：標題與身分過濾
            for song in raw_results:
                title_lower = song["snippet"]["title"].lower()
                channel_lower = song["snippet"]["channelTitle"].lower()
                
                # A. 官方身分檢查 (標題有官方字眼 OR 頻道本身就是官方 VEVO)
                is_official = any(k in title_lower for k in official_keywords) or "vevo" in channel_lower
                
                # B. 排除黑名單 (標題不能有 mix, playlist 等)
                is_blacklisted = any(b in title_lower for b in blacklist)
                
                # C. 歌手名稱檢查 (如果有指定)
                has_artist = True
                if artist_input.strip():
                    has_artist = artist_input.lower() in title_lower or artist_input.lower() in channel_lower
                
                # 綜合判斷：是官方、不是黑名單、且符合歌手
                if is_official and not is_blacklisted and has_artist:
                    final_songs.append(song)

            # 4. 補足機制 (當結果不夠時啟動) 
            if len(final_songs) < 20:
                st.info("💡 正在為您優化搜尋結果，嘗試抓取更多官方單曲...")
                # 補足搜尋：直接找官方 MV，不帶心情詞以增加召回率
                if artist_input.strip():
                    backup_keyword = f"{artist_input} official mv"
                else:
                    backup_keyword = f"{base_query} official music"
                
                backup_results = get_yt_music(backup_keyword)
                
                for song in backup_results:
                    title_lower = song["snippet"]["title"].lower()
                    if any(k in title_lower for k in official_keywords) and not any(b in title_lower for b in blacklist):
                        # 檢查重複與歌手
                        is_duplicate = any(song['id']['videoId'] == s['id']['videoId'] for s in final_songs)
                        artist_check = artist_input.lower() in title_lower if artist_input.strip() else True
                        
                        if not is_duplicate and artist_check:
                            final_songs.append(song)

            # 5. 顯示結果 (去重並排版)
            if final_songs:
                # 根據 videoId 再次確保不重複
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    vid = s['id']['videoId']
                    if vid not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(vid)

                cols = st.columns(2)
                for idx, song in enumerate(unique_songs[:12]): # 顯示前 12 首最精準的
                    with cols[idx % 2]:
                        title = song["snippet"]["title"]
                        video_id = song['id']['videoId']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        st.video(video_url)
                        st.markdown(f"**{title}**")
                        st.write("---")
            else:
                st.warning("⚠️ 找不到符合條件的官方單曲，請嘗試更換心情或檢查歌手名稱。")

        except Exception as e:
            st.error(f"❌ 系統執行出錯：{e}")