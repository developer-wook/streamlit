# 실행: streamlit run deploy/miniproject.py
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="저가형 무료 Q&A", layout="wide")
st.title("저가형 무료 Q&A")

TONE_STYLES = {
    "기본": "친절하고 명확하게 답변.",
    "친근하게": "친구에게 말하듯 편하고 친근한 말투로 답변.",
    "정중하게": "예의를 갖춰 격식있는 존댓말로 답변.",
    "간결하게": "핵심만 짧고 간결하게 답변.",
}


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
    st.subheader("통계")
    log = st.session_state.qa_log
    st.metric("누적 질문 수", len(log))
    avg_len = round(sum(len(qa["answer"]) for qa in log) / len(log)) if log else 0
    st.metric("평균 답변 길이(자)", avg_len)
    if log:
        st.bar_chart({"답변 길이": [len(qa["answer"]) for qa in log]})

    st.subheader("설정")
    tone = st.selectbox("답변 말투", list(TONE_STYLES))
    if st.button("기록 초기화"):
        st.session_state.qa_log = []
        st.rerun()

with left:
    question = st.chat_input("무엇이든 물어보세요")
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
        st.info("질문을 입력하면 아래에 카드로 쌓입니다.")

    for qa in reversed(st.session_state.qa_log):
        with st.expander(f"Q. {qa['question']}"):
            st.markdown(qa["answer"])
