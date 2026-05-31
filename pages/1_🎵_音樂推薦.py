import streamlit as st
from utils.youtube import search_music, get_similar_music
from utils.database import add_favorite

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎵 音樂推薦系統 (YT Music 引擎)")

mood_options = {
    "不指定": "",
    "流行": "top pop hits",
    "憂鬱": "sad emotional ballad",
    "派對": "party dance",
    "音樂劇": "broadway musical",
    "輕音樂放鬆": "relaxing piano ambient",
    "讀書專注": "lofi study beats"
}

selected_mood = st.selectbox("請選擇音樂類型", list(mood_options.keys()))
artist_input = st.text_input("有想搜尋的歌或指定的歌手嗎?", placeholder="例如：Taylor Swift...")

# 狀態初始化
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "view_title" not in st.session_state:
    st.session_state.view_title = "推薦結果"

# 搜尋按鈕
if st.button("幫我挑選音樂"):
    st.session_state.current_page = 1
    with st.spinner("正在前往 YouTube Music 尋找高品質音樂..."):
        query = f"{artist_input} {mood_options[selected_mood]}".strip()
        if not query:
            query = "top pop hits"
        
        results = search_music(query, limit=30)
        if results:
            st.session_state.search_results = results
            st.session_state.view_title = "🔍 搜尋結果"
        else:
            st.session_state.search_results = []
            st.warning("查無符合條件的音樂。")

# --- 分頁與顯示區 ---
def render_pagination(total_pages, key_suffix):
    col_left, col_text, col_right = st.columns([1, 1.5, 1])
    with col_left:
        if st.button("上一頁", key=f"btn_prev_{key_suffix}", use_container_width=True):
            if st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
    with col_text:
        st.markdown(
            f"<div style='text-align: center; line-height: 40px;'>第 {st.session_state.current_page} 頁 / 共 {total_pages} 頁</div>", 
            unsafe_allow_html=True
        )
    with col_right:
        if st.button("下一頁", key=f"btn_next_{key_suffix}", use_container_width=True):
            if st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()

if st.session_state.search_results:
    st.write("---")
    st.subheader(st.session_state.view_title)
    
    items_per_page = 6
    total_results = len(st.session_state.search_results)
    total_pages = (total_results - 1) // items_per_page + 1
    
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = st.session_state.search_results[start_idx:end_idx]

    render_pagination(total_pages, "top")
    st.write("")

    cols = st.columns(2)
    for idx, song in enumerate(page_items):
        with cols[idx % 2]:
            video_id = song["video_id"]
            title = song["title"]
            artist = song["artist"]
            full_title = f"{title} - {artist}"
            
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            st.markdown(f"**{full_title}**")
            
            # 操作按鈕區塊
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("❤️ 加入收藏", key=f"fav_{video_id}"):
                    if add_favorite(st.session_state.username, video_id, full_title):
                        st.success("已加入！")
                    else:
                        st.info("已在清單中！")
            with btn_col2:
                if st.button("🎧 找相似歌曲", key=f"sim_{video_id}"):
                    with st.spinner("正在為您產生專屬電台..."):
                        sim_results = get_similar_music(video_id, limit=30)
                        if sim_results:
                            st.session_state.search_results = sim_results
                            st.session_state.current_page = 1
                            st.session_state.view_title = f"📻 從【{title}】延伸的電台"
                            st.rerun()
                        else:
                            st.warning("找不到相似電台。")
            st.write("---")

    render_pagination(total_pages, "bottom")