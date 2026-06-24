import streamlit as st
from utils.database import add_feedback, get_all_feedback

# 登入檢查
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入才能填寫回饋喔！")
    st.stop()

st.title("💬 留言與回饋")
st.write("您的意見對我們很重要，請告訴我們您的使用心得！")

st.write("---")
st.subheader("📝 填寫回饋")

with st.expander("請點擊此處為我們評分", expanded=True):
    with st.form("my_feedback_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("搜尋結果符合度")
            score_search = st.feedback("stars", key="score_s")
        with col2:
            st.write("私心推薦品質")
            score_rec = st.feedback("stars", key="score_r")
        with col3:
            st.write("整體網站評分")
            score_total = st.feedback("stars", key="score_t")
        
        user_comment = st.text_area(
            "其他建議：", 
            placeholder="例如：私心推薦不好聽、搜尋結果過濾可以寬鬆一點...", 
            help="您的留言將會顯示在下方的留言板中喔！"
        )
        
        if st.form_submit_button("送出評分回饋"):
            # st.feedback 會回傳 0~4，為了方便閱讀我們轉成 1~5 星
            s_score = score_search + 1 if score_search is not None else 0
            r_score = score_rec + 1 if score_rec is not None else 0
            t_score = score_total + 1 if score_total is not None else 0
            
            add_feedback(st.session_state.username, s_score, r_score, t_score, user_comment)
            st.success("感謝您的回饋！我們已成功收到。")
            st.rerun() # 重整頁面讓新留言直接顯示

# --- 留言板顯示區 ---
st.write("---")
st.subheader("📌 使用者留言與站長回覆")

feedbacks = get_all_feedback()

if not feedbacks:
    st.info("目前尚無留言評論，來當第一個留言的人吧！")
else:
    for fb in feedbacks:
        # 只顯示有填寫文字建議的留言
        if fb["comment"] and fb["comment"].strip() != "":
            with st.container():
                # 顯示留言者與時間
                st.caption(f"👤 {fb['username']} • 🕒 {fb['created_at']}")
                
                # 顯示星星分數 (如果有評分的話)
                score_text = ""
                if fb['total_score'] > 0:
                    score_text = f"整體評分: {'⭐' * fb['total_score']}"
                if score_text:
                    st.write(score_text)
                
                # 顯示留言內容
                st.markdown(f"**留言：** {fb['comment']}")
                
                # 顯示站長回覆
                if fb["reply"] and fb["reply"].strip() != "":
                    st.info(f"👨‍💻 站長回覆： {fb['reply']}")
                
                st.write("---") # 增加間距