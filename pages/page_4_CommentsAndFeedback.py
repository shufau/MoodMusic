import streamlit as st
from utils.database import add_feedback, get_all_feedback

# 確保使用者已登入
if not st.session_state.get("logged_in", False):
    st.warning("請先從主頁面登入！！")
    st.stop()

st.title("留言與回饋")
st.write("您的意見對我們很重要，請告訴我們您的使用心得")

st.write("---")
st.subheader("填寫回饋")

with st.expander("請點擊此處為我們評分", expanded=True):
    with st.form("my_feedback_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("搜尋結果符合度")
            score_search = st.feedback("stars", key="score_s")
        with col2:
            st.write("音訊辨識準確度")
            score_audio = st.feedback("stars", key="score_a")
        with col3:
            st.write("整體網站評分")
            score_total = st.feedback("stars", key="score_t")
        
        user_comment = st.text_area(
            "其他建議：", 
            placeholder="例如：音訊辨識不準確、資訊排版不直覺...", 
            help="您的留言將會顯示在下方的留言板中 :)"
        )
        
        if st.form_submit_button("送出評分回饋"):
            s_score = score_search + 1 if score_search is not None else 0
            a_score = score_audio + 1 if score_audio is not None else 0
            t_score = score_total + 1 if score_total is not None else 0
            
            add_feedback(st.session_state.username, s_score, a_score, t_score, user_comment)
            st.success("感謝您的回饋！我們已成功收到。")
            st.rerun() # 重整頁面讓新留言直接顯示


# 留言板顯示區
st.write("---")
st.subheader("使用者留言與站長回覆")

feedbacks = get_all_feedback()

if not feedbacks:
    st.info("目前尚無留言評論，來當第一個留言的人吧！")
else:
    for fb in feedbacks:
        # 只顯示有文字建議的留言
        if fb["comment"] and fb["comment"].strip() != "":
            with st.container():
                # 留言者與時間
                st.caption(f"{fb['username']} • {fb['created_at']}")
                
                # 星星分數
                score_text = ""
                if fb['total_score'] > 0:
                    score_text = f"整體評分: {'⭐' * fb['total_score']}"
                if score_text:
                    st.write(score_text)
                
                # 留言內容
                st.markdown(f"**留言：** {fb['comment']}")
                
                # 站長回覆
                if fb["reply"] and fb["reply"].strip() != "":
                    st.info(f"站長回覆： {fb['reply']}")
                
                st.write("---")