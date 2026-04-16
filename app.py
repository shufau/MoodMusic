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
            
            # 1. 決定基礎參數
            is_long_mode = selected_mood in ["讀書專注", "輕音樂放鬆"]
            target_duration = "any" if is_long_mode else "short"
            search_keyword = f"{artist_input} {base_query}".strip()

            # --- 過濾邏輯函式 (內部使用) ---
            def filter_logic(results, strict=True):
                temp = []
                for song in results:
                    title_lower = song["snippet"]["title"].lower()
                    channel_lower = song["snippet"]["channelTitle"].lower()
                    
                    if is_long_mode:
                        if "ad" not in title_lower: temp.append(song)
                    else:
                        is_blacklisted = any(b in title_lower for b in blacklist)
                        # 檢查標題或頻道是否有歌手名
                        has_artist = True
                        if artist_input.strip():
                            has_artist = artist_input.lower() in title_lower or artist_input.lower() in channel_lower
                        
                        if strict:
                            # 嚴格模式：必須有官方關鍵字
                            is_official = any(k in title_lower for k in official_keywords) or "vevo" in channel_lower
                            if is_official and not is_blacklisted and has_artist:
                                temp.append(song)
                        else:
                            # 寬鬆模式：只要有歌手名且不在黑名單就收
                            if not is_blacklisted and has_artist:
                                temp.append(song)
                return temp

            # --- 階梯式搜尋流程 ---
            
            # 第一層：原始搜尋 (嚴格模式)
            raw_1 = get_yt_music(search_keyword, duration=target_duration)
            final_songs = filter_logic(raw_1, strict=True)

            # 第二層：如果沒歌，改用「寬鬆模式」(去掉官方限制)
            if not final_songs:
                final_songs = filter_logic(raw_1, strict=False)

            # 第三層：如果還是沒歌，連「音樂類別代碼 10」都去掉 (使用自訂搜尋)
            if not final_songs and artist_input.strip():
                # 重新定義一個不限 Category 的搜尋
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                raw_3 = youtube.search().list(
                    q=artist_input.strip(),
                    part="snippet",
                    type="video",
                    maxResults=50,
                    videoDuration="any" # 第三層連長度也放寬，確保一定有影片
                ).execute()["items"]
                final_songs = filter_logic(raw_3, strict=False)

            # 存入 Session State
            if final_songs:
                # 去重邏輯
                unique_songs = []
                seen_ids = set()
                for s in final_songs:
                    vid = s["id"]["videoId"]
                    if vid not in seen_ids:
                        unique_songs.append(s)
                        seen_ids.add(vid)
                st.session_state.search_results = unique_songs[:40]
            else:
                st.session_state.search_results = []
                st.warning("查無符合條件的音樂，連最終搜尋也找不到該歌手。")

        except Exception as e:
            st.error(f"系統執行出錯，請稍後再嘗試")


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