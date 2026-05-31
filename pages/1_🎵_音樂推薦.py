import streamlit as st
from utils.youtube import get_yt_music
from utils.database import add_favorite

if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎵 音樂推薦系統")

mood_options = {"不指定": "", "流行": "top pop hits", "憂鬱": "ballad", "派對": "party dance"}
selected_mood = st.selectbox("請選擇音樂類型", list(mood_options.keys()))
artist_input = st.text_input("有想搜尋的歌手嗎?", placeholder="例如：Taylor Swift")

if st.button("幫我挑選音樂"):
    with st.spinner("正在搜尋中..."):
        query = f"{artist_input} {mood_options[selected_mood]} official audio".strip()
        results = get_yt_music(query)
        
        if results:
            st.session_state.search_results = results
        else:
            st.warning("找不到相關音樂。")

if "search_results" in st.session_state:
    cols = st.columns(2)
    for idx, song in enumerate(st.session_state.search_results[:10]):
        with cols[idx % 2]:
            video_id = song["id"]["videoId"]
            title = song["snippet"]["title"]
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            st.markdown(f"**{title}**")
            
            # 加入收藏按鈕
            if st.button("❤️ 加入收藏", key=f"fav_{video_id}"):
                if add_favorite(st.session_state.username, video_id, title):
                    st.success("已加入收藏！")
                else:
                    st.info("已經在您的收藏清單中了！")
            st.write("---")