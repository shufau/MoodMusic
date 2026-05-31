import streamlit as st
from utils.database import get_favorites, remove_favorite

if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("⭐ 我的收藏清單")

favorites = get_favorites(st.session_state.username)

if not favorites:
    st.info("您目前還沒有收藏任何歌曲哦！快去推薦頁面探索吧。")
else:
    for vid, title in favorites:
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"**{title}**")
            st.video(f"https://www.youtube.com/watch?v={vid}")
        with cols[1]:
            if st.button("❌ 移除收藏", key=f"del_{vid}"):
                remove_favorite(st.session_state.username, vid)
                st.rerun()
        st.write("---")