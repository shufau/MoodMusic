import streamlit as st
from googleapiclient.discovery import build
import json

import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 讀取 API 金鑰
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 官方標示的字詞
official_keywords = [
    "official mv", 
    "official video", 
    "official audio", 
    "official lyric video", 
    "provided to youtube",
    "original mix",
    "vevo"
]

# 欲排除的字詞（黑名單）
blacklist = ["mix", "playlist", "24/7", "hours", "nonstop"]


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


# 存放找到的音樂（才不會因為修改其他選項而消失）
if "search_results" not in st.session_state:
    st.session_state.search_results = None

# 側邊攔
with open("recommendations.json", "r", encoding="utf-8") as f:
    REC_SONGS = json.load(f)

with st.sidebar:
    st.header("站長私心推薦")
    st.caption("如果你不知道聽什麼，試試這些")
    st.write("---")
    
    for song in REC_SONGS:
        st.subheader(song["title"])
        st.video(song["url"])
        st.write("---")


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

selected_mood = st.selectbox("請選擇音樂類型（選擇不指定則預設顯示官方單曲）", list(mood_options.keys()))
artist_input = st.text_input("有想搜尋的歌或指定的歌手嗎?", value="Katy Perry", placeholder="例如：Taylor Swift, Katy Perry, mxmtoon, ...")


# 按鈕觸發邏輯
if st.button("幫我挑選音樂"):
    with st.spinner("正在挑選最適合的音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            # 判定模式
            is_long_mode = selected_mood in ["讀書專注", "輕音樂放鬆"]
            if is_long_mode:
                target_duration = "any"
            else:
                target_duration = "short"
            
            # 初次搜尋
            if artist_input.strip():
                search_keyword = f"{artist_input} {base_query}"
            else:
                search_keyword = base_query

            raw_results = get_yt_music(search_keyword, duration=target_duration)


            # 過濾邏輯函式
            def filter_logic(results):
                temp_list = []
                for song in results:
                    # 轉小寫
                    title_lower = song["snippet"]["title"].lower()
                    channel_lower = song["snippet"]["channelTitle"].lower()
                    
                    if is_long_mode:
                        # 不限官方，不看黑名單，避開廣告就好
                        if "ad" not in title_lower:
                            temp_list.append(song)
                    else:
                        # 官方標示檢查
                        is_official = any(k in title_lower for k in official_keywords) or "vevo" in channel_lower
                        # 黑名單檢查
                        is_blacklisted = any(b in title_lower for b in blacklist)
                        # 歌手檢查
                        has_artist = True
                        if artist_input.strip():
                            has_artist = artist_input.lower() in title_lower or artist_input.lower() in channel_lower
                        
                        if is_official and not is_blacklisted and has_artist:
                            temp_list.append(song)

                return temp_list


            # 首次過濾
            final_songs = filter_logic(raw_results)

            # 補足機制 (當結果少於 10 首時)
            if len(final_songs) < 10:
                # 建立一個備案搜尋清單，按優先順序執行
                backup_queries = []
                
                if not is_long_mode:
                    if artist_input.strip():
                        # 備案 1：搜尋歌手的其他官方 MV
                        backup_queries.append(f"{artist_input} official mv")
                        # 備案 2：最後大絕招，直接搜歌手名字（最寬鬆）
                        backup_queries.append(artist_input.strip())
                    else:
                        backup_queries.append("official music")
                else:
                    if artist_input.strip():
                        backup_queries.append(f"{artist_input} lofi")
                        backup_queries.append(artist_input.strip()) # 歌手長曲備案
                    else:
                        backup_queries.append("lofi")

                # 執行備案搜尋
                for b_query in backup_queries:
                    # 如果已經湊夠 10 首了，就不用再搜下一個備案
                    if len(final_songs) >= 10:
                        break
                        
                    backup_results = get_yt_music(b_query, duration=target_duration)
                    backup_filtered = filter_logic(backup_results)
                    
                    # 合併結果 & 去重
                    existing_ids = {s["id"]["videoId"] for s in final_songs}
                    for s in backup_filtered:
                        if s["id"]["videoId"] not in existing_ids:
                            final_songs.append(s)

            # 將搜尋結果存入記憶體
            if final_songs:
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    vid = s["id"]["videoId"]
                    if vid not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(vid)
                
                # 把處理好的 40 首歌存進記憶體
                st.session_state.search_results = unique_songs[:40]
            else:
                st.session_state.search_results = [] # 沒結果也要清空舊記憶
                st.warning("查無符合條件的音樂，請嘗試更換選項或歌手。")

        except Exception as e:
            st.error(f"系統執行出錯，請稍後再嘗試 ;(")
            # st.error(f"錯誤訊息：{e}")


# 獨立顯示結果的區塊
if st.session_state.search_results:
    cols = st.columns(2)
    for idx, song in enumerate(st.session_state.search_results):
        with cols[idx % 2]:
            title = song["snippet"]["title"]
            video_id = song["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            st.video(video_url)
            st.markdown(f"**{title}**")
            st.write("---")


# 使用者評分回饋區
st.write("---")
st.subheader("您的意見對我們很重要")

# 建立評分區塊
with st.expander("請點擊此處為我們評分"):
    # 使用 st.form（隔離區，讓網站不會因為此處變更而重整）
    with st.form("my_feedback_form", clear_on_submit=True):
        # 使用唯一的 key 確保不會衝突
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("搜尋結果符合度")
            score_search = st.feedback("stars", key="score_s")
        with col2:
            st.write("私心推薦品質")
            score_rec = st.feedback("stars", key="score_r")
        with col3:
            st.write("整體網站評分")
            score_total = st.feedback("stars", key="score_t")
        
        user_comment = st.text_area("其他建議：",placeholder="例如：希望能增加更多音樂劇推薦、搜尋結果過濾可以寬鬆一點...",help="請放心填寫，您的建議將會匿名傳送給我們，作為未來優化的重要參考。", key="user_msg")
        
        if st.form_submit_button("送出評分回饋"):
            try:
                # 準備新資料（要跟試算表欄位名稱相同）
                new_data = pd.DataFrame({
                    "時間": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "搜尋符合度": [score_search + 1 if score_search is not None else None],
                    "推薦品質": [score_rec + 1 if score_rec is not None else None],
                    "整體評分": [score_total + 1 if score_total is not None else None],
                    "其他建議": [user_comment]
                })
                
                # 讀取現有資料並追加 (TTL=0 確保不讀取舊快取)
                existing_data = conn.read(ttl=0)
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                
                # 寫回 Google Sheets
                conn.update(data=updated_df)
                st.success("感謝您的回饋！我們已成功收到。")
            except Exception as e:
                st.error(f"寫入失敗，請檢查 Secrets 設定。錯誤內容：{e}")