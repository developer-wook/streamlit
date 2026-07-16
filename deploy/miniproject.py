# 실행: streamlit run deploy/miniproject.py
import streamlit as st
from openai import OpenAI

PALETTE = {
    "teal": "#3DAFA0",
    "coral": "#FF7F6B",
    "amber": "#E0A428",
    "violet": "#8E7CC3",
}

st.set_page_config(page_title="가볍게 물어보는 Q&A", layout="wide")
st.title("가볍게 물어보는 Q&A")
st.markdown(
    f'<div style="height:6px;border-radius:3px;margin-bottom:20px;'
    f'background:linear-gradient(90deg,{PALETTE["teal"]},{PALETTE["coral"]},'
    f'{PALETTE["amber"]},{PALETTE["violet"]});"></div>',
    unsafe_allow_html=True,
)

TONE_STYLES = {
    "기본": "친절하고 명확하게 답변.",
    "친근하게": "친구에게 말하듯 편하고 친근한 말투로 답변.",
    "정중하게": "예의를 갖춰 격식있는 존댓말로 답변.",
    "간결하게": "핵심만 짧고 간결하게 답변.",
}
TONE_COLORS = {
    "기본": PALETTE["teal"],
    "친근하게": PALETTE["coral"],
    "정중하게": PALETTE["violet"],
    "간결하게": PALETTE["amber"],
}


def stat_tile(label, value, color):
    st.markdown(
        f'<div style="background:{color}1A;border:1px solid {color};border-radius:10px;'
        f'padding:10px 14px;margin-bottom:10px;">'
        f'<div style="font-size:13px;color:#666;">{label}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{color};">{value}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_client():
    return OpenAI(
        api_key=st.secrets["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def ask(question, history, tone):
    client = get_client()
    system = {"role": "system", "content": TONE_STYLES[tone]}
    messages = [system] + history + [{"role": "user", "content": question}]
    stream = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


if "qa_log" not in st.session_state:
    st.session_state.qa_log = []

left, right = st.columns([3, 1])

with right:
    with st.container(border=True):
        st.subheader("지금까지")
        log = st.session_state.qa_log
        stat_tile("질문 수", len(log), PALETTE["teal"])
        avg_len = round(sum(len(qa["answer"]) for qa in log) / len(log)) if log else 0
        stat_tile("평균 답변 길이(자)", avg_len, PALETTE["coral"])
        if log:
            st.bar_chart({"답변 길이": [len(qa["answer"]) for qa in log]}, color=PALETTE["violet"])

    with st.container(border=True):
        st.subheader("말투 고르기")
        tone = st.selectbox("답변 말투", list(TONE_STYLES))
        st.markdown(
            f'<span style="background:{TONE_COLORS[tone]};color:white;padding:3px 12px;'
            f'border-radius:12px;font-size:12px;">{tone}</span>',
            unsafe_allow_html=True,
        )
        if st.button("새로 시작하기"):
            st.session_state.qa_log = []
            st.rerun()

with left:
    question = st.chat_input("무엇이든 편하게 물어보세요")
    if question:
        history = []
        for qa in st.session_state.qa_log:
            history.append({"role": "user", "content": qa["question"]})
            history.append({"role": "assistant", "content": qa["answer"]})

        with st.status("답변 작성 중...", expanded=False) as status:
            answer = "".join(ask(question, history, tone))
            status.update(label="답변 완료", state="complete")

        st.session_state.qa_log.append({"question": question, "answer": answer})
        st.rerun()

    if not st.session_state.qa_log:
        st.info("질문 하나 던져보세요.")

    for qa in reversed(st.session_state.qa_log):
        with st.expander(f"Q. {qa['question']}"):
            st.markdown(qa["answer"])