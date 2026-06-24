import streamlit as st
from supabase import create_client
import hashlib
from datetime import datetime
import pytz

# 初始化 Supabase 連線，使用 @st.cache_resource 避免重複連線
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        # 檢查帳號是否已存在
        existing = supabase.table("users").select("*").eq("username", username).execute()
        if len(existing.data) > 0:
            return False
            
        # 寫入新帳號
        supabase.table("users").insert({
            "username": username,
            "password": hash_password(password)
        }).execute()
        return True
    except Exception as e:
        st.error(f"建立使用者錯誤: {e}")
        return False

def verify_user(username, password):
    hashed_pw = hash_password(password)
    result = supabase.table("users").select("*").eq("username", username).eq("password", hashed_pw).execute()
    # 如果有抓到資料，代表帳號密碼吻合
    return len(result.data) > 0

def add_favorite(username, video_id, title):
    try:
        # 檢查是否已收藏過
        existing = supabase.table("favorites").select("*").eq("username", username).eq("video_id", video_id).execute()
        if len(existing.data) > 0:
            return False 
        
        # 寫入收藏
        supabase.table("favorites").insert({
            "username": username,
            "video_id": video_id,
            "title": title
        }).execute()
        return True
    except Exception as e:
        return False

def get_favorites(username):
    result = supabase.table("favorites").select("video_id, title").eq("username", username).execute()
    # 將回傳的 list of dict 轉換回 [(vid, title), ...] 格式
    return [(row["video_id"], row["title"]) for row in result.data]

def remove_favorite(username, video_id):
    supabase.table("favorites").delete().eq("username", username).eq("video_id", video_id).execute()
    return True

def add_feedback(username, search_score, audio_score, total_score, comment):
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.now(tw_tz)
    tw_time_str = now_tw.strftime("%Y-%m-%d %H:%M:%S")
    
    supabase.table("feedback").insert({
        "username": username,
        "search_score": search_score,
        "audio_score": audio_score,
        "total_score": total_score,
        "comment": comment,
        "reply": "",
        "created_at": tw_time_str
    }).execute()

def get_all_feedback():
    # 利用 Supabase 內建功能依照時間遞減排序
    result = supabase.table("feedback").select("*").order("created_at", desc=True).execute()
    return result.data