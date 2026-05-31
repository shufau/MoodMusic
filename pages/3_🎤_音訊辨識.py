import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import librosa
import librosa.display
import yt_dlp  # 👈 強大的 YouTube 下載套件
from utils.audio_rec import run_audio_recognition
from utils.youtube import search_music, get_similar_music
from utils.database import add_favorite

# 確保使用者已完全登入且資料存在
if not st.session_state.get("logged_in", False) or "username" not in st.session_state:
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎤 音訊辨識與深度分析")
st.write("上傳音樂片段，或從推薦清單直接傳送歌曲，我們將為您進行專業的聲學特徵分析！")

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# ==========================================
# 🌟 核心重構：把龐大的分析邏輯封裝成共用函式
# ==========================================
def process_and_analyze(temp_path, known_song_name=None):
    try:
        # 若是透過遠端按鈕傳來的，就跳過 Shazam 辨識
        if known_song_name:
            song_name = known_song_name
        else:
            song_name = run_audio_recognition(temp_path)
            
        y, sr = librosa.load(temp_path, sr=None)
        
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm_value = round(float(tempo[0])) if isinstance(tempo, (np.ndarray, list)) else round(float(tempo))
        
        rms = np.mean(librosa.feature.rms(y=y))
        energy_score = float(min(100, (rms / 0.3) * 100))
        
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        brightness_score = float(min(100, (centroid / 4000) * 100))
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        beat_strength = np.mean(onset_env)
        dance_score = float(min(100, (beat_strength / 2.0) * 100))
        
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

        yt_results = []
        if song_name:
            yt_results = search_music(song_name, limit=4)
            
        st.session_state.analysis_results = {
            "song_name": song_name, "bpm": bpm_value, "energy": energy_score,
            "brightness": brightness_score, "danceability": dance_score,
            "happy_prob": happy_prob, "electronic_prob": electronic_prob,
            "party_prob": party_prob, "vocal_prob": vocal_prob,
            "yt_results": yt_results, "audio_data": y, "sample_rate": sr
        }
    except Exception as e:
        st.error(f"分析過程發生錯誤: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ==========================================
# 🌟 攔截區：處理從別的分頁傳來的「遠端分析請求」
# ==========================================
if st.session_state.get("yt_analyze_request"):
    req = st.session_state.yt_analyze_request
    st.session_state.yt_analyze_request = None # 執行一次後立即清空，避免無限迴圈
    
    st.info(f"📥 正在從 YouTube 提取音訊：**{req['title']}** ...")
    temp_dl_path = f"temp_{req['video_id']}.m4a"
    
    # yt-dlp 的下載設定：只抓音訊，存成 m4a 格式
    # 🛡️ yt-dlp 終極武裝下載設定
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': temp_dl_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,         # 忽略 SSL 憑證檢查
        'source_address': '0.0.0.0',        # 🌟 核心破解 1：強制使用 IPv4，避開 IPv6 封鎖
        'extractor_args': {
            # 🌟 核心破解 2：改偽裝成 iOS 或 TV APP，目前防護較低
            'youtube': ['player_client=ios,tv,web'] 
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with st.spinner("⏳ 正在下載高音質音訊，請稍候... (約需 5~10 秒)"):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={req['video_id']}"])
                
        with st.spinner("🎧 音訊下載完成！正在啟動本地端聲學分析..."):
            process_and_analyze(temp_dl_path, known_song_name=req['title'])
            st.rerun() # 分析完畢，重整畫面顯示圖表
    except Exception as e:
        st.error(f"YouTube 載入失敗，可能遇到版權限制或網路問題：{e}")

# --- 原本的使用者上手動上傳檔案區塊 ---
uploaded_file = st.file_uploader("或者您也可以手動上傳音訊檔案 (建議 5~15 秒)", type=["mp3", "wav", "m4a", "ogg"])
if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')
    if st.button("啟動辨識與深度分析"):
        with st.spinner("🎧 正在聆聽並啟動本地端聲學分析..."):
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            process_and_analyze(temp_path)


# ---------------------------------------------------------
# ✨ 畫面渲染區：獨立於按鈕之外！只要快取裡有資料，畫面就維持顯示
# ---------------------------------------------------------
if st.session_state.analysis_results is not None:
    res = st.session_state.analysis_results
    
    st.write("---")
    st.subheader("📊 本地端音樂特徵分析 (由 Librosa 驅動)")
    st.markdown(f"### ⏱️ 偵測 BPM: `{res['bpm']}` 拍/分鐘")
    
    col_chart, col_radar = st.columns([1.2, 1])
    with col_chart:
        st.caption("聲學視覺化圖表")
        fig, ax = plt.subplots(nrows=2, sharex=True, figsize=(6, 4))
        fig.patch.set_facecolor('#0E1117')
        librosa.display.waveshow(res['audio_data'], sr=res['sample_rate'], ax=ax[0], color='#1DB954')
        ax[0].set(title='Waveform (波形)')
        ax[0].title.set_color('white')
        ax[0].tick_params(colors='white')
        D = librosa.amplitude_to_db(np.abs(librosa.stft(res['audio_data'])), ref=np.max)
        librosa.display.specshow(D, y_axis='hz', x_axis='time', sr=res['sample_rate'], ax=ax[1], cmap='magma')
        ax[1].set(title='Spectrogram (頻譜)')
        ax[1].title.set_color('white')
        ax[1].tick_params(colors='white')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig) 
        
    with col_radar:
        st.caption("AI 模擬特徵雷達圖 (滿分 100)")
        categories = ['能量與爆發力 (Energy)', '聲音明亮度 (Brightness)', '節奏打擊感 (Danceability)']
        values = [res['energy'], res['brightness'], res['danceability']]
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]], fill='toself', line_color='#1DB954'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.write("---")
    st.subheader("🎛️ 進階聲學推測儀表板 (AI Heuristics)")
    st.write("基於頻譜特徵、調性分析與人聲頻段演算法，為您預測歌曲屬性：")
    
    dash_col1, dash_col2 = st.columns(2)
    def draw_progress_bar(val, left_label, right_label, color_emoji):
        try:
            val_float = float(val)
            if np.isnan(val_float): val_float = 50.0
        except:
            val_float = 50.0
        val_int = int(max(0, min(100, val_float)))
        st.markdown(f"**{color_emoji} {left_label}** `{val_int}%` ↔ `{100-val_int}%` **{right_label}**")
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

    if res['song_name']:
        st.write("---")
        st.success(f"🎵 歌曲分析對象： **{res['song_name']}**")
        
        # 隱藏底下原本從 Shazam 回傳產生的 youtube search，
        # 因為我們現在已經是直接對 youtube 影片做分析了！