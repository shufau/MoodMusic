import streamlit as st
import plotly.graph_objects as go
from utils.spotify import get_recommendations, get_audio_features
from utils.youtube import get_best_video
from utils.database import add_favorite

if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！")
    st.stop()

st.title("🎵 專業音樂數據推薦 (Spotify x YouTube)")
st.write("結合 Spotify 強大的數據分析大腦，為您精準挑選音樂。")

# Spotify 支援的種子曲風 (Seed Genres)
mood_options = {
    "流行 (Pop)": "pop",
    "派對 (Party)": "party",
    "憂鬱 (Sad)": "sad",
    "讀書專注 (Study)": "study",
    "放鬆 (Chill)": "chill",
    "重金屬 (Heavy Metal)": "heavy-metal",
    "浪漫 (Romance)": "romance"
}

selected_mood = st.selectbox("請選擇您現在的心情或情境", list(mood_options.keys()))

if st.button("啟動 Spotify 大腦推薦"):
    genre = mood_options[selected_mood]
    with st.spinner("🧠 正在與 Spotify 伺服器連線，計算最佳歌單..."):
        spotify_tracks = get_recommendations(genre, limit=5)
        st.session_state.spotify_results = spotify_tracks

# 顯示推薦結果
if st.session_state.get("spotify_results"):
    st.write("---")
    
    for track in st.session_state.spotify_results:
        st.subheader(f"🎧 {track['title']} - {track['artist']}")
        
        # 將畫面切成左右兩半 (左邊影片，右邊數據)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.spinner("正在尋找 YouTube 影片..."):
                video_id = get_best_video(f"{track['title']} {track['artist']}")
                if video_id:
                    st.video(f"https://www.youtube.com/watch?v={video_id}")
                    if st.button("❤️ 加入收藏", key=f"fav_{track['id']}"):
                        if add_favorite(st.session_state.username, video_id, f"{track['title']} - {track['artist']}"):
                            st.success("已加入收藏！")
                        else:
                            st.info("已在清單中！")
                else:
                    st.warning("YouTube 找不到這首歌的影片。")
                    
        with col2:
            with st.spinner("讀取 Spotify 音樂特徵..."):
                features = get_audio_features(track['id'])
                if features:
                    st.markdown(f"**⏱️ 節奏速度 (BPM):** `{features['bpm']}`")
                    st.markdown(f"**🎹 歌曲調性 (Key):** `{features['key']}`")
                    
                    # 繪製 Plotly 雷達圖
                    categories = ['適合跳舞 (Danceability)', '能量值 (Energy)', '正向情緒 (Valence)', '原聲度 (Acoustic)']
                    values = [
                        features['danceability'] * 100, 
                        features['energy'] * 100, 
                        features['valence'] * 100, 
                        features['acousticness'] * 100
                    ]
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=values + [values[0]], # 閉合雷達圖
                        theta=categories + [categories[0]],
                        fill='toself',
                        line_color='#1DB954' # Spotify 綠色
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False,
                        margin=dict(l=20, r=20, t=20, b=20),
                        height=250,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("無法取得此歌曲的數據。")
        st.write("---")