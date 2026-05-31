import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import streamlit as st

# 初始化 Spotify API 連線
def get_spotify_client():
    client_id = st.secrets["SPOTIFY_CLIENT_ID"]
    client_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

sp = get_spotify_client()

def get_recommendations(mood_genre, limit=10):
    """根據曲風向 Spotify 請求精準推薦"""
    try:
        # Spotify 內建的種子曲風 (可根據心情對應)
        results = sp.recommendations(seed_genres=[mood_genre], limit=limit)
        tracks = []
        for track in results['tracks']:
            tracks.append({
                "id": track['id'],
                "title": track['name'],
                "artist": ", ".join([artist['name'] for artist in track['artists']])
            })
        return tracks
    except Exception as e:
        st.error(f"Spotify 推薦發生錯誤: {e}")
        return []

def get_audio_features(track_id):
    """取得歌曲的 BPM、調性、情緒等深度數據"""
    try:
        features = sp.audio_features(track_id)[0]
        
        # 將 Spotify 的調性數字 (0-11) 轉換成人類看得懂的音符
        key_mapping = {0: 'C', 1: 'C#', 2: 'D', 3: 'D#', 4: 'E', 5: 'F', 6: 'F#', 7: 'G', 8: 'G#', 9: 'A', 10: 'A#', 11: 'B'}
        key_str = key_mapping.get(features['key'], 'Unknown')
        mode_str = "Major (大調)" if features['mode'] == 1 else "Minor (小調)"
        
        return {
            "bpm": round(features['tempo']),
            "key": f"{key_str} {mode_str}",
            "danceability": features['danceability'],
            "energy": features['energy'],
            "valence": features['valence'],
            "acousticness": features['acousticness']
        }
    except Exception as e:
        return None