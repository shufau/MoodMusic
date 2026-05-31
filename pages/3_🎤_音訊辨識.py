import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
from utils.audio_rec import run_audio_recognition
from utils.youtube import search_music  # 👈 這裡換成了新的 search_music
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
    
    if st.button("開始辨識與分析"):
        with st.spinner("🎧 正在聆聽並比對資料庫..."):
            # 暫存檔案讓 shazamio 與 librosa 讀取
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # 1. 執行 Shazam 辨識
                song_name = run_audio_recognition(temp_path)
                
                if song_name:
                    st.success(f"🎉 辨識成功！這首歌是： **{song_name}**")
                    
                    # --- 音訊視覺化 ---
                    st.write("---")
                    st.subheader("📊 專業音訊視覺化分析")
                    with st.spinner("正在繪製音訊頻譜圖..."):
                        y, sr = librosa.load(temp_path, sr=None)
                        fig, ax = plt.subplots(nrows=2, sharex=True, figsize=(10, 6))
                        fig.patch.set_facecolor('#0E1117')
                        
                        librosa.display.waveshow(y, sr=sr, ax=ax[0], color='#1DB954')
                        ax[0].set(title='Waveform (音量隨時間變化)')
                        ax[0].title.set_color('white')
                        ax[0].tick_params(colors='white')
                        
                        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
                        img = librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=sr, ax=ax[1], cmap='magma')
                        ax[1].set(title='Spectrogram (頻率與能量分佈)')
                        ax[1].title.set_color('white')
                        ax[1].tick_params(colors='white')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                    
                    # --- YouTube 搜尋 (使用新引擎) ---
                    st.write("---")
                    st.subheader("為您在 YouTube 上尋找這首歌：")
                    
                    # 呼叫新版的 search_music，抓取 4 筆結果
                    yt_results = search_music(song_name, limit=4)
                    
                    if yt_results:
                        cols = st.columns(2)
                        for idx, song in enumerate(yt_results):
                            with cols[idx % 2]:
                                # 新引擎回傳的資料格式
                                video_id = song["video_id"]
                                full_title = f"{song['title']} - {song['artist']}"
                                
                                st.video(f"https://www.youtube.com/watch?v={video_id}")
                                st.markdown(f"**{full_title}**")
                                
                                if st.button("❤️ 加入收藏", key=f"rec_fav_{video_id}"):
                                    if add_favorite(st.session_state.username, video_id, full_title):
                                        st.success("已加入收藏！")
                                    else:
                                        st.info("已經在您的收藏清單中了！")
                                st.write("---")
                    else:
                        st.warning("YouTube 找不到這首歌的相關影片。")
                else:
                    st.error("抱歉，無法辨識這首歌曲，請嘗試上傳更清晰或更長的片段。")
            finally:
                # 刪除暫存檔
                if os.path.exists(temp_path):
                    os.remove(temp_path)