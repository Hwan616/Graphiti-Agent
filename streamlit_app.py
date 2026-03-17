import streamlit as st
from openai import OpenAI
import json
import os

# --- 1. 설정 및 JSON 데이터 로드 ---
def load_config():
    config_path = os.path.join(".venv", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

config = load_config()

# 페이지 설정
st.set_page_config(page_title="OpenAI Chatbot", page_icon="🤖")
st.title("OpenAI API 챗봇")

# --- 2. OpenAI 클라이언트 및 세션 초기화 ---
# API 키 확인
api_key = config.get("OPENAI_API_KEY") if config else None

if not api_key:
    st.error(".venv/config.json에서 OPENAI_API_KEY를 찾을 수 없습니다.")
    st.stop()

# 클라이언트 생성
client = OpenAI(api_key=api_key)

# Streamlit 세션 상태에 대화 내역 저장 (없으면 빈 리스트로 초기화)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 채팅 메시지 표시 ---
# 저장된 모든 대화 내역을 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 대화 로직 실행 ---
if prompt := st.chat_input("질문을 입력하세요..."):
    # 1) 사용자 입력 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) OpenAI API를 호출하여 답변 생성
    with st.chat_message("assistant"):
        # 실시간 응답(Streaming)을 위한 플레이스홀더
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # API 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini", # 혹은 "gpt-4-turbo"
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True, # 실시간으로 글자가 써지는 효과
            )
            
            # 스트리밍 결과 처리
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")

    # 3) 어시스턴트 답변을 세션 내역에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})