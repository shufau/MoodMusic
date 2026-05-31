import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import librosa
import librosa.display
from utils.audio_rec import run_audio_recognition
from utils.youtube import search_music, get_similar_music
from utils.database import add_favorite

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎤 音訊辨識與分析")
st.write("上傳音樂片段，我們不只幫您找歌，還會為您進行聲學特徵分析！")

uploaded_file = st.file_uploader("上傳音訊檔案", type=["mp3", "wav", "m4a", "ogg"])

# 初始化一個 Session State 變數來持久化儲存分析結果
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')
    
    # 當按下按鈕時，只負責運算，並把結果塞進緩存，不把顯示畫面綁死在這裡
    if st.button("啟動辨識與深度分析"):
        with st.spinner("🎧 正在聆聽並啟動本地端聲學分析..."):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                # 執行辨識
                song_name = run_audio_recognition(temp_path)
                
                # 載入音檔並計算基礎聲學特徵
                y, sr = librosa.load(temp_path, sr=None)
                
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                if isinstance(tempo, (np.ndarray, list)):
                    bpm_value = round(float(tempo[0]))
                else:
                    bpm_value = round(float(tempo))
                
                rms = np.mean(librosa.feature.rms(y=y))
                energy_score = float(min(100, (rms / 0.3) * 100))
                
                centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
                brightness_score = float(min(100, (centroid / 4000) * 100))
                
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                beat_strength = np.mean(onset_env)
                dance_score = float(min(100, (beat_strength / 2.0) * 100))
                
                # ==========================================
                # 進階 AI 特徵運算區塊
                # ==========================================
                
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                chroma_mean = np.mean(chroma, axis=1)
                major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
                minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
                
                corr_major = np.corrcoef(chroma_mean, major_profile)
                major_corr = corr_major[0, 1] if isinstance(corr_major, np.ndarray) and corr_major.ndim == 2 else 0.0
                if np.isnan(major_corr): major_corr = 0.0
                
                corr_minor = np.corrcoef(chroma_mean, minor_profile)
                minor_corr = corr_minor[0, 1] if isinstance(corr_minor, np.ndarray) and corr_minor.ndim == 2 else 0.0
                if np.isnan(minor_corr): minor_corr = 0.0
                
                happy_prob = float(max(0, min(100, (major_corr - minor_corr + 1) / 2 * 100)))
                
                electronic_prob = float(max(0, min(100, (centroid - 800) / 2500 * 100)))
                if np.isnan(electronic_prob): electronic_prob = 50.0
                
                party_prob = float(min(100, (energy_score * 0.4 + dance_score * 0.6)))
                if np.isnan(party_prob): party_prob = 50.0
                
                S = np.abs(librosa.stft(y))
                freqs = librosa.fft_frequencies(sr=sr)
                vocal_band = (freqs > 300) & (freqs < 3000)
                vocal_energy = np.sum(S[vocal_band, :])
                total_energy = np.sum(S)
                
                if total_energy == 0:
                    vocal_prob = 0.0
                else:
                    vocal_prob = float(max(0, min(100, (vocal_energy / total_energy) * 150)))
                if np.isnan(vocal_prob): vocal_prob = 50.0
                
                # ==========================================

                yt_results = []
                if song_name:
                    yt_results = search_music(song_name, limit=4)
                    
                st.session_state.analysis_results = {
                    "song_name": song_name,
                    "bpm": bpm_value,
                    "energy": energy_score,
                    "brightness": brightness_score,
                    "danceability": dance_score,
                    "happy_prob": happy_prob,
                    "electronic_prob": electronic_prob,
                    "party_prob": party_prob,
                    "vocal_prob": vocal_prob,
                    "yt_results": yt_results,
                    "audio_data": y,
                    "sample_rate": sr
                }
            except Exception as e:
                st.error(f"分析過程發生錯誤: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# ---------------------------------------------------------
# 畫面渲染區：獨立於按鈕之外，只要快取裡有資料，畫面就維持顯示
# ---------------------------------------------------------
if st.session_state.analysis_results is not None:
    res = st.session_state.analysis_results
    
    st.write("---")
    st.subheader("📊 音樂特徵分析（由 Librosa 驅動）")
    st.markdown(f"### ⏱️ 偵測 BPM：`{res['bpm']}` 拍/分鐘")
    
    col_chart, col_radar = st.columns([1.2, 1])
    
    with col_chart:
        st.caption("聲學視覺化圖表")
        fig, ax = plt.subplots(nrows=2, sharex=True, figsize=(6, 4))
        fig.patch.set_facecolor('#0E1117')
        
        librosa.display.waveshow(res['audio_data'], sr=res['sample_rate'], ax=ax[0], color='#1DB954')
        ax[0].set(title='Waveform（波形）')
        ax[0].title.set_color('white')
        ax[0].tick_params(colors='white')
        
        D = librosa.amplitude_to_db(np.abs(librosa.stft(res['audio_data'])), ref=np.max)
        librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=res['sample_rate'], ax=ax[1], cmap='magma')
        ax[1].set(title='Spectrogram（頻譜）')
        ax[1].title.set_color('white')
        ax[1].tick_params(colors='white')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig) 
        
    with col_radar:
        st.caption("AI 模擬特徵雷達圖（滿分 100）")
        categories = ['能量與爆發力（Energy）', '聲音明亮度（Brightness）', '節奏打擊感（Danceability）']
        values = [res['energy'], res['brightness'], res['danceability']]
        
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

    # ==========================================
    # 進階 AI 推測儀表板 (進度條)
    # ==========================================
    st.write("---")
    st.subheader("🎛️ 進階聲學推測儀表板 (AI Heuristics)")
    st.write("基於頻譜特徵、調性分析與人聲頻段演算法，為您預測歌曲屬性：")
    
    dash_col1, dash_col2 = st.columns(2)
    
    # 🛠️ 完美的 HTML Flexbox 對齊排版
    def draw_progress_bar(val, left_label, right_label, color_emoji):
        try:
            val_float = float(val)
            if np.isnan(val_float):
                val_float = 50.0
        except Exception:
            val_float = 50.0
            
        val_int = int(max(0, min(100, val_float)))
        
        html_str = f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span><b>{color_emoji} {left_label}</b> <code>{val_int}%</code></span>
            <span><code>{100-val_int}%</code> <b>{right_label}</b></span>
        </div>
        """
        st.markdown(html_str, unsafe_allow_html=True)
        st.progress(val_int)

    with dash_col1:
        draw_progress_bar(res['happy_prob'], "陽光大調 (Happy)", "憂鬱小調 (Sad)", "🎭")
        st.caption("基於色譜圖 (Chromagram) 餘弦相似度比對")
        
        st.write("") 
        draw_progress_bar(res['electronic_prob'], "電子合成 (Electronic)", "原聲樂器 (Acoustic)", "🎸")
        st.caption("基於頻譜質心 (Spectral Centroid) 頻率分佈")

    with dash_col2:
        draw_progress_bar(res['party_prob'], "派對狂歡 (Party)", "放鬆平緩 (Chill)", "🍷")
        st.caption("綜合 RMS 能量與 Onset 節奏爆發力計算")
        
        st.write("") 
        draw_progress_bar(res['vocal_prob'], "人聲演唱 (Vocal)", "純音樂 (Instrumental)", "🎤")
        st.caption("分析核心人聲頻段 (300-3000Hz) 能量佔比")
    # ==========================================

    if res['song_name']:
        st.write("---")
        st.success(f"🎉 Shazam 辨識成功！這首歌是： **{res['song_name']}**")
        st.subheader("為您在 YouTube 上尋找完整歌曲：")
        
        if res['yt_results']:
            cols = st.columns(2)
            for idx, song in enumerate(res['yt_results']):
                with cols[idx % 2]:
                    video_id = song["video_id"]
                    full_title = f"{song['title']} - {song['artist']}"
                    
                    st.video(f"https://www.youtube.com/watch?v={video_id}")
                    st.markdown(f"**{full_title}**")
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("❤️ 加入收藏", key=f"rec_fav_{video_id}"):
                            if add_favorite(st.session_state.username, video_id, full_title):
                                st.success("已加入收藏！")
                            else:
                                st.info("已經在清單中了！")
                                
                    with btn_col2:
                        if st.button("🎧 找相似歌曲", key=f"rec_sim_{video_id}"):
                            with st.spinner("正在為您產生專屬電台..."):
                                sim_results = get_similar_music(video_id, limit=30)
                                if sim_results:
                                    st.session_state.search_results = sim_results
                                    st.session_state.current_page = 1
                                    st.session_state.view_title = f"📻 從【{song['title']}】延伸的電台"
                                    st.switch_page("pages/1_🎵_音樂推薦.py")
                                else:
                                    st.warning("找不到相似電台。")
                    st.write("---")
        else:
            st.warning("YouTube 找不到這首歌的相關影片。")
    else:
        st.error("抱歉，歌曲辨識失敗，但我們依然為您完成了聲學分析！")