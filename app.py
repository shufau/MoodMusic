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

# 最少要有幾首歌
MIN_RESULTS = 8


# 去 Youtube 抓資料
def get_yt_music(query, duration="short", use_music_category=True):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    # 建立基礎參數
    search_params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 50,
        "videoDuration": duration
    }

    # 只有當 use_music_category 為 True 時才加入類別限制
    if use_music_category:
        search_params["videoCategoryId"] = "10"
    
    search_response = youtube.search().list(**search_params).execute()
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
artist_input = st.text_input("有想搜尋的歌或指定的歌手嗎?", placeholder="例如：Taylor Swift, Katy Perry, mxmtoon, ...")


# 按鈕觸發邏輯
if st.button("幫我挑選音樂"):
    st.session_state.current_page = 1
    with st.spinner("正在挑選最適合的音樂..."):
        try:
            base_query = mood_options[selected_mood]
            final_songs = []
            
            is_long_mode = selected_mood in ["讀書專注", "輕音樂放鬆"]
            target_duration = "any" if is_long_mode else "short"

            # 內部的統一搜尋與過濾工具
            def fetch_and_filter(query, strict, use_cat10):
                results = get_yt_music(query, duration=target_duration, use_music_category=use_cat10)
                temp = []
                for song in results:
                    title_lower = song["snippet"]["title"].lower()
                    channel_lower = song["snippet"]["channelTitle"].lower()
                    
                    if is_long_mode:
                        if "ad" not in title_lower: temp.append(song)
                    else:
                        is_blacklisted = any(b in title_lower for b in blacklist)
                        # 檢查歌手（只有在有輸入歌手時才檢查）
                        has_artist = True
                        if artist_input.strip():
                            has_artist = artist_input.lower() in title_lower or artist_input.lower() in channel_lower
                        
                        if strict:
                            is_official = any(k in title_lower for k in official_keywords) or "vevo" in channel_lower
                            if is_official and not is_blacklisted and has_artist:
                                temp.append(song)
                        else:
                            if not is_blacklisted and has_artist:
                                temp.append(song)
                return temp

            # --- 核心邏輯：區分「有歌手」與「無歌手」 ---
            
            artist_name = artist_input.strip()

            if artist_name:
                # 【情境 A：有指定歌手】
                # 第一層：歌手 + 心情 + 官方 + 類別10
                q1 = f"{artist_name} {base_query}".strip()
                final_songs = fetch_and_filter(q1, strict=True, use_cat10=True)

                # 第二層：歌手 + 官方
                if len(final_songs) < MIN_RESULTS:
                    q2 = f"{artist_name} official".strip()
                    final_songs = fetch_and_filter(q2, strict=True, use_cat10=False)

                # 第三層：歌手全開 (不限官方、不限類別)
                if len(final_songs) < MIN_RESULTS:
                    final_songs = fetch_and_filter(artist_name, strict=False, use_cat10=False)
            
            else:
                # 【情境 B：沒有指定歌手】
                # 第一層：心情 + "official mv" + 類別10
                if base_query:
                    q1 = f"{base_query} official mv"
                    final_songs = fetch_and_filter(q1, strict=True, use_cat10=True)
                
                # 第二層：直接推薦熱門 "official mv" + 類別10
                if len(final_songs) < MIN_RESULTS:
                    q2 = "official mv"
                    final_songs = fetch_and_filter(q2, strict=True, use_cat10=True)

            # --- 結果處理 ---
            if final_songs:
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
                st.warning("查無符合條件的音樂。")

        except Exception as e:
            # st.error(f"系統執行出錯，請稍後再嘗試")
            st.error(f"今日的 YOUTUBE API 搜尋次數額度滿了，請體諒窮大學生 ;)")


# 頁數選擇功能
def render_pagination(total_pages, key_suffix):
    # 建立 3 欄，比例設為 [1, 1.5, 1]，讓中間文字區間稍微寬一點
    col_left, col_text, col_right = st.columns([1, 1.5, 1])
    
    with col_left:
        if st.button("上一頁", key=f"btn_prev_{key_suffix}", use_container_width=True):
            if st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()

    with col_text:
        # 使用 HTML 讓文字在欄位內水平置中，並微調間距使其與按鈕對齊
        st.markdown(
            f"""
            <div style='text-align: center; line-height: 40px;'>
                第 {st.session_state.current_page} 頁 / 共 {total_pages} 頁
            </div>
            """, 
            unsafe_allow_html=True
        )

    with col_right:
        if st.button("下一頁", key=f"btn_next_{key_suffix}", use_container_width=True):
            if st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()


# 存放找到的音樂與當前頁碼
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 獨立顯示結果的區塊
if st.session_state.search_results:
    # --- 分頁基礎計算 ---
    items_per_page = 6
    total_results = len(st.session_state.search_results)
    total_pages = (total_results - 1) // items_per_page + 1
    
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = st.session_state.search_results[start_idx:end_idx]

    # --- 1. 上方分頁列 ---
    st.write("---")
    render_pagination(total_pages, "top")
    st.write("")
    st.write("")

    # --- 2. 影片顯示區 ---
    cols = st.columns(2)
    num_items = len(page_items) # 取得當前頁面的影片總數

    for idx, song in enumerate(page_items):
        with cols[idx % 2]:
            title = song["snippet"]["title"]
            video_id = song["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            st.video(video_url)
            st.markdown(f"**{title}**")
            
            if idx < num_items - 2:
                st.write("---")
            elif num_items % 2 != 0 and idx == num_items - 1:
                pass 
            elif idx < num_items - (2 if num_items % 2 == 0 else 1):
                st.write("---")

    # --- 3. 下方分頁列 ---
    st.write("")
    st.write("")
    render_pagination(total_pages, "bottom")


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


# 在留言板顯示區的最上方加入這一行
st.markdown('<div id="comment_section"></div>', unsafe_allow_html=True)
# --- 留言板顯示區 ---
st.write("---")
st.subheader("使用者留言與站長回覆")

try:
    # 讀取最新資料 (TTL=0 確保抓到最新留言)
    feedback_df = conn.read(ttl=0)
    
    # 確保資料表中有「時間」欄位並進行排序（最新的在前）
    if not feedback_df.empty and "時間" in feedback_df.columns:
        feedback_df = feedback_df.sort_values(by="時間", ascending=False)
        
        # 檢查是否有名為「站長回覆」的欄位，若沒有則建立空欄位避免報錯
        if "站長回覆" not in feedback_df.columns:
            feedback_df["站長回覆"] = ""

        # 只顯示有填寫「其他建議」的留言
        valid_comments = feedback_df[feedback_df["其他建議"].notna() & (feedback_df["其他建議"] != "")]

        if not valid_comments.empty:
            for _, row in valid_comments.iterrows():
                with st.container():
                    # 顯示留言時間與內容
                    st.caption(f"{row['時間']}")
                    st.markdown(f"{row['其他建議']}")
                    
                    # 顯示站長回覆 (如果有內容的話)
                    reply = row.get("站長回覆", "")
                    if pd.notna(reply) and str(reply).strip() != "":
                        st.info(f"站長回覆： {reply}")
                    
                    st.write("") # 增加間距
        else:
            st.info("目前尚無留言評論。")
    else:
        st.info("目前尚無資料。")

except Exception as e:
    st.error(f"讀取留言失敗：{e}")


# 浮動按鈕的 CSS 樣式與跳轉連結
st.markdown("""
    <style>
    /* 浮動按鈕樣式 */
    .floating-button {
        position: fixed;
        bottom: 60px; /* 位置往上調 */
        right: 20px;
        /* 設定為半透明紅色：255, 75, 75 是 Streamlit 紅色，0.6 是透明度 */
        background-color: rgba(255, 75, 75, 0.6); 
        color: white !important;
        padding: 12px 20px;
        border-radius: 50px;
        text-decoration: none !important;
        font-weight: bold;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        z-index: 999999;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        /* 毛玻璃效果 */
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        /* 邊框增加質感 */
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .floating-button:hover {
        transform: scale(1.1);
        /* 懸停時稍微加深紅色，讓互動感更強 */
        background-color: rgba(255, 75, 75, 0.9);
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.5);
    }
    
    /* 平滑滾動效果 */
    html {
        scroll-behavior: smooth;
    }
    </style>
    
    <a href="#comment_section" class="floating-button">
        查看留言
    </a>
    """, unsafe_allow_html=True)