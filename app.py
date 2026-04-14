import streamlit as st
from googleapiclient.discovery import build
import json

# 讀取 API 金鑰
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]


# 去 Youtube 抓資料
def get_yt_music(query, duration="short"):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=50,
        videoCategoryId="10",
        videoDuration=duration
    ).execute()
    
    return search_response["items"]


# 側邊攔
with open('recommendations.json', 'r', encoding='utf-8') as f:
    REC_SONGS = json.load(f)

with st.sidebar:
    st.header("站長私心推薦")
    st.write("如果你不知道聽什麼，試試這些：")
    
    for song in REC_SONGS:
        st.subheader(song["title"])
        st.video(song["url"])
        st.caption(song["caption"])


# 網頁介面
st.set_page_config(page_title="音樂推薦系統", page_icon="🎧")
st.title("音樂推薦系統")

mood_options = {
    "不指定": "",
    "流行": "top pop hits",
    "憂鬱": "ballad",
    "派對": "party dance",
    "音樂劇": "broadway musical soundtrack",
    "輕音樂放鬆": "relaxing piano ambient",
    "讀書專注": "lofi study"
}

selected_mood = st.selectbox("請選擇音樂類型", list(mood_options.keys()))
artist_input = st.text_input("你有想聽的歌手嗎？", placeholder="例如：Taylor Swift, Katy Perry, Juicy J, ...")


# 按鈕觸發邏輯
if st.button("幫我挑選音樂"):
    with st.spinner("正在挑選最適合的音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            # 判定模式
            is_long_mode = selected_mood in ["讀書專注", "輕音樂放鬆"]
            target_duration = "any" if is_long_mode else "short"
            
            official_keywords = [
                "official mv", 
                "official video", 
                "official audio", 
                "official lyric video", 
                "provided to youtube",
                "original mix",
                "vevo"
            ]
            blacklist = ["mix", "playlist", "24/7", "hours", "nonstop"]

            # 初次搜尋
            search_keyword = f"{artist_input} {base_query}" if artist_input.strip() else base_query
            raw_results = get_yt_music(search_keyword, duration=target_duration)


            # 封裝過濾邏輯以便重複使用
            def filter_logic(results):
                temp_list = []
                for song in results:
                    title_lower = song["snippet"]["title"].lower()
                    channel_lower = song["snippet"]["channelTitle"].lower()
                    
                    if is_long_mode:
                        # 長模式：不限官方，不看黑名單，避開廣告即可
                        if "ad" not in title_lower:
                            temp_list.append(song)
                    else:
                        # 單曲模式：嚴格官方檢查
                        is_official = any(k in title_lower for k in official_keywords) or "vevo" in channel_lower
                        is_blacklisted = any(b in title_lower for b in blacklist)
                        has_artist = True
                        if artist_input.strip():
                            has_artist = artist_input.lower() in title_lower or artist_input.lower() in channel_lower
                        
                        if is_official and not is_blacklisted and has_artist:
                            temp_list.append(song)
                return temp_list


            # 執行第一次過濾
            final_songs = filter_logic(raw_results)

            # 補足機制 (當結果少於 10 首時啟動)
            if len(final_songs) < 10:
                if not is_long_mode:
                    # 如果是單曲模式，強制搜尋官方 MV
                    backup_query = f"{artist_input} official mv" if artist_input.strip() else "official music video top hits"
                else:
                    # 補足策略：如果是長模式，搜尋相關的長時播放清單
                    backup_query = f"{artist_input} {base_query} lofi" if artist_input.strip() else f"{base_query} meditation music"

                backup_results = get_yt_music(backup_query, duration=target_duration)
                backup_filtered = filter_logic(backup_results)
                
                # 合併結果並去重
                existing_ids = {s['id']['videoId'] for s in final_songs}
                for s in backup_filtered:
                    if s['id']['videoId'] not in existing_ids:
                        final_songs.append(s)

            # 4. 顯示結果
            if final_songs:
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    vid = s['id']['videoId']
                    if vid not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(vid)

                cols = st.columns(2)
                for idx, song in enumerate(unique_songs[:40]):
                    with cols[idx % 2]:
                        title = song["snippet"]["title"]
                        video_id = song['id']['videoId']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        st.video(video_url)
                        st.markdown(f"**{title}**")
                        st.write("---")
            else:
                st.warning("查無符合條件的音樂，請嘗試更換關鍵字。")

        except Exception as e:
            st.error(f"系統執行出錯：{e}")