import streamlit as st
import os
import asyncio
import nest_asyncio
from datetime import datetime, timezone
from openai import OpenAI
from graphiti_core import Graphiti
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. 비동기 패치 (최상단 필수)
nest_asyncio.apply()

st.set_page_config(page_title="Graphiti Agent")
st.title("Graphiti Agent")
st.caption("OpenAI 기반 장기 기억 지식 그래프 에이전트")

# --- 2. 세션 검증 ---
if not st.session_state.get("config_loaded"):
    st.error("초기 설정이 로드되지 않았습니다.")
    if st.button("Home으로 이동"):
        st.switch_page("streamlit_app.py")
    st.stop()

# --- 3. 기반 유틸리티 함수 ---

def run_async(coro):
    """비동기 함수를 동기식 루프에서 실행"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def get_graphiti():
    os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
    
    # 1. Graphiti 인스턴스 생성 (URI는 원래대로 neo4j+s:// 사용)
    g = Graphiti(
        uri=st.session_state.neo4j_config["uri"],
        user=st.session_state.neo4j_config["user"],
        password=st.session_state.neo4j_config["password"]
    )
    
    # 2. [슈퍼 패치] 모든 세션 생성 시 데이터베이스 이름을 강제로 지정
    # 이 부분은 Graphiti가 내부적으로 어떤 이름을 부르든 무조건 d1653294로 연결하게 만듭니다.
    actual_db_name = "d1653294" 
    
    # 몽키 패치: 드라이버의 session 메서드를 가로챕니다.
    original_session = g.driver.session

    def patched_session(*args, **kwargs):
        # 호출 시 database 인자가 있으면 우리 이름으로 바꿉니다.
        kwargs["database"] = actual_db_name
        return original_session(*args, **kwargs)

    # 가로챈 메서드로 교체
    g.driver.session = patched_session
    
    # 라이브러리 내부 속성도 혹시 모르니 변경
    if hasattr(g, 'database'):
        g.database = actual_db_name
        
    return g

def generate_episode_summary(user_text, ai_text):
    """대화 내용을 바탕으로 5단어 내외의 짧은 요약(제목)을 생성합니다."""
    client = OpenAI(api_key=st.session_state.openai_api_key)
    summary_prompt = f"""
    다음 대화 내용을 Neo4j 노드의 제목으로 사용할 수 있도록 5단어 내외의 아주 짧은 한 줄로 요약해줘.
    예: 'BeArrow 앱 배포 일정 논의', '로봇 청소기 장애물 회피 로직'
    
    사용자: {user_text}
    AI: {ai_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        # 따옴표나 마침표 제거 후 반환
        return response.choices[0].message.content.strip().replace('"', '').replace("'", "").replace(".", "")
    except:
        return f"Chat_{datetime.now().strftime('%H%M%S')}" # 에러 시 기본값

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def generate_final_answer(user_query, context_facts):
    """OpenAI를 사용한 최종 답변 생성"""
    client = OpenAI(api_key=st.session_state.openai_api_key)
    
    context_text = "\n".join([f"- {fact}" for fact in context_facts]) if context_facts else "관련 기록 없음."
    
    sys_prompt = f"""
	1. Persona (정체성)
	- 당신은 [장기 기억 지식 그래프]를 탑재한 지능형 개인 비서입니다.
	- 사용자의 과거 대화 내용, 선호도, 경험을 모두 기억하고 이를 바탕으로 초개인화된 답변을 제공합니다.
	
	2. Context & Knowledge Source (지식 소스 및 우선순위)
	- 답변의 최우선 근거는 아래 제공되는 [장기 기억 컨텍스트]입니다.
	- 제공된 컨텍스트와 당신의 일반 지식이 충돌할 경우, 반드시 [장기 기억 컨텍스트]를 우선시하십시오.
	- 컨텍스트에 없는 내용을 추측하여 답변하지 마십시오.
	
	3. Reasoning Logic (추론 로직)
	1. 질문이 들어오면 먼저 [장기 기억 컨텍스트] 내에 관련 정보가 있는지 탐색하십시오.
	2. 정보가 있다면: 해당 정보를 구체적으로 언급하며 답변을 구성하십시오. (예: "지난번에 말씀하신 ~에 따르면...")
	3. 정보가 부족하다면: "제 기억에는 관련 내용이 없지만, ..."이라고 명시하며 일반 지식을 활용하십시오.
	4. 정보가 전혀 없다면: 솔직하게 모른다고 답하고 사용자에게 질문을 던져 정보를 보완하십시오.
	
	4. Constraints & Guardrails (제약 사항)
	- 언어: 반드시 한국어를 사용하며, 정중하고 친근한 어조를 유지하십시오.
	- 보안: 사용자의 개인정보나 API 키 등 민감한 정보는 절대 언급하지 마십시오.
	- 형식: 가독성을 위해 마크다운(Markdown) 형식을 적극 활용하십시오.
	
	5. Output Format (출력 형식)
	- 답변은 간결하면서도 핵심을 짚어야 합니다.
	- 필요한 경우 번호 매기기나 글머리 기호를 사용하십시오.
	
	[장기 기억 컨텍스트]
	{context_text}
	"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content

# --- 4. 채팅 UI 및 로직 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "context" in msg and msg["context"]:
            with st.expander("참고한 기억"):
                st.caption(msg["context"])

# 사용자 입력 처리
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    full_response = ""
    retrieved_facts = []

    try:
        g_instance = get_graphiti()

        # A. 검색 (Retrieve)
        with st.status("지식 그래프 탐색 중...", expanded=False) as status:
            run_async(g_instance.build_indices_and_constraints())
            search_results = run_async(g_instance.search(prompt))
            
            if search_results:
                # 1. 만약 .results 속성이 있는 객체라면
                if hasattr(search_results, 'results'):
                    retrieved_facts = [res.fact for res in search_results.results]
                # 2. 만약 이미 리스트 형태라면 바로 순회
                elif isinstance(search_results, list):
                    retrieved_facts = [res.fact if hasattr(res, 'fact') else str(res) for res in search_results]

        # B. 답변 생성 (Generate)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = generate_final_answer(prompt, retrieved_facts)
            message_placeholder.markdown(full_response)
            
            context_str = "\n".join([f"- {f}" for f in retrieved_facts]) if retrieved_facts else ""
            if context_str:
                with st.expander("참고한 기억"):
                    st.caption(context_str)

        # C. 저장 (Ingest) - 명시적 진행 상태 표시
        with st.status("새로운 기억을 저장 중...", expanded=False) as status:
            try:
                run_async(g_instance.add_episode(
                    name=f"Chat_{datetime.now().strftime('%H%M%S')}",
                    episode_body=f"User: {prompt}\nAssistant: {full_response}",
                    source_description=generate_episode_summary(prompt, full_response),
                    reference_time=datetime.now(timezone.utc)
                ))
                status.update(label="Successed: 기억 저장 완료", state="complete")
            except Exception as e:
                status.update(label="Failed: 기억 저장 실패", state="error")
                st.error(f"저장 오류: {e}")

    except Exception as e:
        st.error(f"System Error: {e}")

    # 세션 기록 업데이트
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "context": context_str if retrieved_facts else None
    })