import streamlit as st
from utils.database import add_favorite
from utils.youtube import get_similar_music

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！！")
    st.stop()

st.title("站長私心推薦")
st.write("這裡是我們親自挑選的歌，不知道要聽什麼時可以來看看 :)")
st.write("---")

# 自訂歌單區
curated_songs = [
    {
        "video_id": "kJQP7kiw5Fk", 
        "title": "Despacito", 
        "artist": "Luis Fonsi"
    },
    {
        "video_id": "dQw4w9WgXcQ", 
        "title": "Never Gonna Give You Up", 
        "artist": "Rick Astley"
    }
]

# 畫面排版
cols = st.columns(2)

for idx, song in enumerate(curated_songs):
    with cols[idx % 2]:
        vid = song["video_id"]
        title = song["title"]
        artist = song["artist"]
        full_title = f"{title} - {artist}"
        
        # 顯示 YouTube 影片與標題
        st.video(f"https://www.youtube.com/watch?v={vid}")
        st.markdown(f"**{full_title}**")
        
        # 操作按鈕
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("加入收藏", key=f"curated_fav_{vid}"):
                if add_favorite(st.session_state.username, vid, full_title):
                    st.success("已加入！！")
                else:
                    st.info("已在清單中！！")
                    
        with btn_col2:
            if st.button("找相似歌曲", key=f"curated_sim_{vid}"):
                with st.spinner("正在為您產生專屬電台..."):
                    sim_results = get_similar_music(vid, limit=30)
                    if sim_results:
                        # 儲存結果並設定推薦頁面的標題狀態
                        st.session_state.search_results = sim_results
                        st.session_state.current_page = 1

                        # 簡化標題文字顯示 (切掉後面的歌手名)
                        display_title = full_title.split(" - ")[0]
                        st.session_state.view_title = f"從【{display_title}】延伸的電台"
                        
                        # # 跳轉回搜尋頁面
                        st.switch_page("pages/page_1_MusicRecommendations.py")
                    else:
                        st.warning("找不到相似電台。")
        st.write("---")