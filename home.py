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
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# 세션 초기화
if "config_loaded" not in st.session_state:
    st.session_state.config_loaded = False

# --- 2. 설정 확인 및 테스트 UI ---
config = load_config()

if not config:
    st.error("❌ `.venv/config.json` 파일을 찾을 수 없습니다. 경로와 파일명을 확인해 주세요. README.md의 설정 가이드를 참고하세요.")
    st.stop()

if st.button("연결 테스트 및 세션 활성화"):
    with st.spinner("서버 연결 확인 중..."):
        try:
            # 1. Neo4j 연결 테스트 (동기 드라이버 사용)
            driver = GraphDatabase.driver(
                config['NEO4J_URI'], 
                auth=(config['NEO4J_USER'], config['NEO4J_PASSWORD'])
            )
            with driver.session() as session:
                session.run("RETURN 1").single()
            driver.close()
            
            # 2. OpenAI API 테스트
            client = OpenAI(api_key=config['OPENAI_API_KEY'])
            client.models.list()

            # 3. 세션 데이터 전역 저장
            st.session_state.openai_api_key = config['OPENAI_API_KEY']
            st.session_state.neo4j_config = {
                "uri": config['NEO4J_URI'],
                "user": config['NEO4J_USER'],
                "password": config['NEO4J_PASSWORD']
            }
            st.session_state.config_loaded = True
            
            st.balloons()
            st.success("Connection successed")
            
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.session_state.config_loaded = False