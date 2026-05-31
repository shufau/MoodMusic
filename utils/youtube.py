from ytmusicapi import YTMusic
import streamlit as st

ytmusic = YTMusic()

def search_music(query, limit=20):
    """用於有明確『歌手』或『歌名』的精確搜尋"""
    try:
        results = ytmusic.search(query, filter="songs", limit=limit)
        if not results:
            results = ytmusic.search(query, limit=limit)
            
        formatted_results = []
        for item in results:
            if item.get("videoId"):
                creators = item.get("artists") or item.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                formatted_results.append({
                    "video_id": item["videoId"],
                    "title": item["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"搜尋發生錯誤: {e}")
        return []

def search_by_style(style_keyword, limit=30):
    """用於只有『風格』時，直接找該風格的精選播放清單並抽取歌曲"""
    try:
        # 找該風格的最熱門播放清單
        playlists = ytmusic.search(style_keyword, filter="playlists", limit=1)
        
        # 如果找不到播放清單，退回一般搜尋
        if not playlists:
            return search_music(style_keyword, limit)
        
        # 抓取該播放清單裡面的所有歌曲
        browse_id = playlists[0]['browseId']
        playlist_data = ytmusic.get_playlist(browse_id, limit=limit)
        
        formatted_results = []
        for track in playlist_data.get('tracks', []):
            if track.get("videoId"):
                creators = track.get("artists") or track.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                formatted_results.append({
                    "video_id": track["videoId"],
                    "title": track["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"風格搜尋發生錯誤: {e}")
        return []

def get_similar_music(video_id, limit=20):
    """根據給定的歌曲 ID，取得曲風相似的推薦歌單"""
    try:
        playlist = ytmusic.get_watch_playlist(videoId=video_id, limit=limit)
        tracks = playlist.get("tracks", [])
        
        formatted_results = []
        for song in tracks[1:]:
            if song.get("videoId"):
                creators = song.get("artists") or song.get("authors") or [{"name": "Unknown"}]
                artist_name = ", ".join([a["name"] for a in creators])
                formatted_results.append({
                    "video_id": song["videoId"],
                    "title": song["title"],
                    "artist": artist_name
                })
        return formatted_results
    except Exception as e:
        st.error(f"取得相似歌曲發生錯誤: {e}")
        return []