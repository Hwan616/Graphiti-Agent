import streamlit as st
import json
import os
from neo4j import GraphDatabase
from openai import OpenAI

st.set_page_config(page_title="Graph Memory")

st.title("AI Agent based Graph Memory")
st.markdown("본 페이지는 프로젝트의 기반 설정을 로드하고 서버 연결을 확인합니다.")

# --- 1. 설정 파일 로드 함수 ---
def load_config():
    config_path = os.path.join(".venv", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

# 세션 초기화
if "config_loaded" not in st.session_state:
    st.session_state.config_loaded = False

# --- 2. 설정 확인 및 테스트 UI ---
config = load_config()

final_config = {}

if config:
    st.success("`.venv/config.json` 파일을 성공적으로 로드했습니다.")
    final_config = config
else:
    st.warning("설정 파일을 찾을 수 없습니다. 아래 정보를 직접 입력해 주세요.")
    
    # 2단 컬럼으로 입력창 배치
    col1, col2 = st.columns(2)
    with col1:
        neo4j_uri = st.text_input("Neo4j URI", value="neo4j+s://")
        neo4j_user = st.text_input("Neo4j User", value="neo4j")
    with col2:
        neo4j_password = st.text_input("Neo4j Password", type="password")
        openai_key = st.text_input("OpenAI API Key", type="password")
    
    # 입력된 값을 final_config에 할당
    final_config = {
        'NEO4J_URI': neo4j_uri,
        'NEO4J_USER': neo4j_user,
        'NEO4J_PASSWORD': neo4j_password,
        'OPENAI_API_KEY': openai_key
    }

if st.button("연결 테스트 및 세션 활성화"):
    with st.spinner("서버 연결 확인 중..."):
        try:
            # 1. Neo4j 연결 테스트 (동기 드라이버 사용)
            driver = GraphDatabase.driver(
                final_config['NEO4J_URI'], 
                auth=(final_config['NEO4J_USER'], final_config['NEO4J_PASSWORD'])
            )
            with driver.session() as session:
                session.run("RETURN 1").single()
            driver.close()
            
            # 2. OpenAI API 테스트
            client = OpenAI(api_key=final_config['OPENAI_API_KEY'])
            client.models.list()

            # 3. 세션 데이터 전역 저장
            st.session_state.openai_api_key = final_config['OPENAI_API_KEY']
            st.session_state.neo4j_config = {
                "uri": final_config['NEO4J_URI'],
                "user": final_config['NEO4J_USER'],
                "password": final_config['NEO4J_PASSWORD']
            }
            st.session_state.config_loaded = True
            
            st.balloons()
            st.success("Connection successed")
            
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.session_state.config_loaded = False