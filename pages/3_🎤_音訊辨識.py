import streamlit as st
import os
from utils.audio_rec import run_audio_recognition
from utils.youtube import get_yt_music
from utils.database import add_favorite

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎤 音訊辨識 (找歌神器)")
st.write("上傳一小段您錄下的音樂片段，系統將為您辨識出歌曲名稱！(支援 mp3, wav, m4a)")

uploaded_file = st.file_uploader("上傳音訊檔案", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')
    
    if st.button("開始辨識"):
        with st.spinner("🎧 正在聆聽並比對資料庫..."):
            # 暫存檔案讓 shazamio 讀取
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                song_name = run_audio_recognition(temp_path)
                if song_name:
                    st.success(f"🎉 辨識成功！這首歌是： **{song_name}**")
                    
                    st.subheader("為您在 YouTube 上尋找這首歌：")
                    yt_results = get_yt_music(song_name)
                    
                    if yt_results:
                        # 使用 columns 來排列，一排顯示兩個
                        cols = st.columns(2)
                        # 最多顯示 6 筆結果就好，免得版面太長
                        for idx, song in enumerate(yt_results[:6]):
                            with cols[idx % 2]:
                                video_id = song["id"]["videoId"]
                                title = song["snippet"]["title"]
                                
                                st.video(f"https://www.youtube.com/watch?v={video_id}")
                                st.markdown(f"**{title}**")
                                
                                # 加入收藏按鈕
                                if st.button("❤️ 加入收藏", key=f"rec_fav_{video_id}"):
                                    if add_favorite(st.session_state.username, video_id, title):
                                        st.success("已加入收藏！")
                                    else:
                                        st.info("已經在您的收藏清單中了！")
                                
                                st.write("---")
                    else:
                        st.warning("YouTube 找不到這首歌的相關影片。")
                else:
                    st.error("抱歉，無法辨識這首歌曲，請嘗試上傳更清晰或更長的片段。")
            finally:
                # 無論成功或失敗，都要刪除暫存檔，避免佔用伺服器空間
                if os.path.exists(temp_path):
                    os.remove(temp_path)