import streamlit as st
from utils.database import get_favorites, remove_favorite
from utils.youtube import get_similar_music

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("⭐ 我的收藏清單")
st.write("這裡記錄了您喜愛的音樂，您可以隨時播放或以此延伸專屬電台。")

# 從 Supabase 撈出該使用者的收藏清單
favorites = get_favorites(st.session_state.username)

if not favorites:
    st.info("您的收藏清單空空如也，快去聽歌點愛心吧！")
else:
    # 使用 2 欄排版美化畫面
    cols = st.columns(2)
    for idx, song in enumerate(favorites):
        with cols[idx % 2]:
            
            # 👇 核心修復：改用數字 0 和 1 來讀取 List 中的資料
            video_id = song[0]
            full_title = song[1]
            
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            st.markdown(f"**{full_title}**")
            
            # 雙排操作按鈕區
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("❌ 移除收藏", key=f"del_{video_id}"):
                    if remove_favorite(st.session_state.username, video_id):
                        st.success("已成功移除！")
                        st.rerun()  # 立即重新整理畫面
                    else:
                        st.error("移除失敗，請稍後再試。")
                        
            with btn_col2:
                if st.button("🎧 找相似歌曲", key=f"fav_sim_{video_id}"):
                    with st.spinner("正在產生專屬電台..."):
                        sim_results = get_similar_music(video_id, limit=30)
                        if sim_results:
                            # 儲存結果並設定推薦頁面的標題狀態
                            st.session_state.search_results = sim_results
                            st.session_state.current_page = 1
                            
                            # 簡化標題文字顯示 (切掉後面的歌手名)
                            display_title = full_title.split(" - ")[0]
                            st.session_state.view_title = f"📻 從收藏【{display_title}】延伸的電台"
                            
                            # ⚡ 跨頁面跳轉
                            st.switch_page("pages/1_🎵_音樂推薦.py")
                        else:
                            st.warning("找不到相似電台。")
            st.write("---")