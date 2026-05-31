import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import librosa
import librosa.display
from utils.audio_rec import run_audio_recognition
from utils.youtube import search_music
from utils.database import add_favorite

if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎤 音訊辨識與深度分析")
st.write("上傳音樂片段，我們不只幫您找歌，還會在本地端為您進行專業的聲學特徵分析！")

uploaded_file = st.file_uploader("上傳音訊檔案 (建議 5~15 秒)", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')
    
    if st.button("啟動辨識與深度分析"):
        with st.spinner("🎧 正在聆聽並啟動本地端聲學分析..."):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # --- 第一部分：辨識歌名 ---
                song_name = run_audio_recognition(temp_path)
                
                # --- 第二部分：Librosa 本地端特徵萃取 (我們的迷你 Spotify 演算法) ---
                st.write("---")
                st.subheader("📊 本地端音樂特徵分析 (由 Librosa 驅動)")
                
                # 載入音檔
                y, sr = librosa.load(temp_path, sr=None)
                
                # 1. 萃取 BPM (節奏速度)
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                bpm_value = round(float(np.atleast_1d(tempo)[0]))
                
                # 2. 萃取 RMS 能量 (並轉換為 0-100 的分數，假設 0.3 為極大聲)
                rms = np.mean(librosa.feature.rms(y=y))
                energy_score = min(100, (rms / 0.3) * 100)
                
                # 3. 萃取 頻譜質心/明亮度 (轉換為 0-100，假設 4000Hz 為極限)
                centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
                brightness_score = min(100, (centroid / 4000) * 100)
                
                # 4. 萃取 節奏強度/Onset (轉換為 0-100)
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                beat_strength = np.mean(onset_env)
                dance_score = min(100, (beat_strength / 2.0) * 100) # 依經驗值 2.0 為非常強烈的鼓聲
                
                # 顯示 BPM
                st.markdown(f"### ⏱️ 偵測 BPM: `{bpm_value}` 拍/分鐘")
                
                # 將畫面分為左右兩邊：左邊雷達圖，右邊傳統圖表
                col_chart, col_radar = st.columns([1.2, 1])
                
                with col_chart:
                    st.caption("聲學視覺化圖表")
                    fig, ax = plt.subplots(nrows=2, sharex=True, figsize=(6, 4))
                    fig.patch.set_facecolor('#0E1117')
                    
                    librosa.display.waveshow(y, sr=sr, ax=ax[0], color='#1DB954')
                    ax[0].set(title='Waveform (波形)')
                    ax[0].title.set_color('white')
                    ax[0].tick_params(colors='white')
                    
                    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
                    librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=sr, ax=ax[1], cmap='magma')
                    ax[1].set(title='Spectrogram (頻譜)')
                    ax[1].title.set_color('white')
                    ax[1].tick_params(colors='white')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                
                with col_radar:
                    st.caption("AI 模擬特徵雷達圖 (滿分 100)")
                    categories = ['能量與爆發力 (Energy)', '聲音明亮度 (Brightness)', '節奏打擊感 (Danceability)']
                    values = [energy_score, brightness_score, dance_score]
                    
                    fig_radar = go.Figure(data=go.Scatterpolar(
                        r=values + [values[0]], 
                        theta=categories + [categories[0]],
                        fill='toself',
                        line_color='#1DB954'
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        margin=dict(l=30, r=30, t=30, b=30),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                # --- 第三部分：尋找 YouTube ---
                if song_name:
                    st.write("---")
                    st.success(f"🎉 Shazam 辨識成功！這首歌是： **{song_name}**")
                    st.subheader("為您在 YouTube 上尋找完整歌曲：")
                    
                    yt_results = search_music(song_name, limit=4)
                    
                    if yt_results:
                        cols = st.columns(2)
                        for idx, song in enumerate(yt_results):
                            with cols[idx % 2]:
                                video_id = song["video_id"]
                                full_title = f"{song['title']} - {song['artist']}"
                                
                                st.video(f"https://www.youtube.com/watch?v={video_id}")
                                st.markdown(f"**{full_title}**")
                                
                                if st.button("❤️ 加入收藏", key=f"rec_fav_{video_id}"):
                                    if add_favorite(st.session_state.username, video_id, full_title):
                                        st.success("已加入收藏！")
                                    else:
                                        st.info("已經在清單中了！")
                                st.write("---")
                    else:
                        st.warning("YouTube 找不到這首歌的相關影片。")
                else:
                    st.error("抱歉，歌曲辨識失敗，但我們依然為您完成了聲學分析！請嘗試上傳更清晰的片段以獲得歌名。")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)