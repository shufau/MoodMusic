import streamlit as st
from utils.database import init_db, create_user, verify_user

st.set_page_config(page_title="音樂推薦系統 - 登入", page_icon="🎧")

# 初始化資料庫
init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🎧 歡迎來到音樂推薦系統")
    tab1, tab2 = st.tabs(["登入", "註冊"])
    
    with tab1:
        st.subheader("登入您的帳號")
        login_user = st.text_input("帳號", key="login_user")
        login_pwd = st.text_input("密碼", type="password", key="login_pwd")
        if st.button("登入"):
            if verify_user(login_user, login_pwd):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success("登入成功！請稍候...")
                st.rerun()
            else:
                st.error("帳號或密碼錯誤！")
                
    with tab2:
        st.subheader("建立新帳號")
        reg_user = st.text_input("新帳號", key="reg_user")
        reg_pwd = st.text_input("新密碼", type="password", key="reg_pwd")
        if st.button("註冊"):
            if reg_user and reg_pwd:
                if create_user(reg_user, reg_pwd):
                    st.success("註冊成功！請至「登入」分頁進行登入。")
                else:
                    st.error("此帳號已被使用，請換一個。")
            else:
                st.warning("請填寫帳號與密碼。")
else:
    st.title(f"👋 歡迎回來，{st.session_state.username}！")
    st.write("請使用左側選單開始探索音樂、查看收藏或辨識歌曲。")
    if st.button("登出"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()