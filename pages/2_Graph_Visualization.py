import streamlit as st
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
import json
import os

st.set_page_config(page_title="Graph Visualization")
st.title("Graph Visualizer")
st.caption("Neo4j 데이터베이스에 저장된 실시간 그래프를 시각화합니다.")

# --- 1. 세션 검증 ---
if not st.session_state.get("config_loaded"):
    st.error("초기 설정이 로드되지 않았습니다.")
    if st.button("Home으로 이동"):
        st.switch_page("home.py")
    st.stop()

# --- 2. 기반 정보 설정 ---
config = st.session_state.neo4j_config
DB_NAME = config['user']

# --- 3. 데이터 로드 및 초기화 함수 ---
def get_graph_data():
    """Neo4j에서 노드와 관계 데이터를 가져와 agraph 형식으로 변환합니다."""
    nodes = []
    edges = []
    
    driver = GraphDatabase.driver(config['uri'], auth=(config['user'], config['password']))
    try:
        with driver.session(database=DB_NAME) as session:
            # 모든 노드와 관계를 가져오는 쿼리
            query = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100"
            results = session.run(query)
            
            node_ids = set()
            for record in results:
                n, r, m = record['n'], record['r'], record['m']
                
                # 노드 처리 (n)
                if n.element_id not in node_ids:
                    label = list(n.labels)[0] if n.labels else "Unknown"
                    color = "#F87171" if label == "Entity" else "#60A5FA" # Entity: 빨강, Episodic: 파랑
                    nodes.append(Node(id=n.element_id, label=n.get('name', 'No Name'), color=color, size=20))
                    node_ids.add(n.element_id)
                
                # 노드 처리 (m)
                if m.element_id not in node_ids:
                    label = list(m.labels)[0] if m.labels else "Unknown"
                    color = "#F87171" if label == "Entity" else "#60A5FA"
                    nodes.append(Node(id=m.element_id, label=m.get('name', 'No Name'), color=color, size=20))
                    node_ids.add(m.element_id)
                
                # 관계 처리
                edges.append(Edge(source=n.element_id, target=m.element_id, label=r.type))
    finally:
        driver.close()
    return nodes, edges

def reset_database():
    """데이터베이스의 모든 내용을 삭제합니다. (매우 주의!)"""
    driver = GraphDatabase.driver(config['uri'], auth=(config['user'], config['password']))
    try:
        with driver.session(database=DB_NAME) as session:
            session.run("MATCH (n) DETACH DELETE n")
        return True
    except Exception as e:
        st.error(f"초기화 중 오류 발생: {e}")
        return False
    finally:
        driver.close()

# --- 4. 사이드바 컨트롤 ---
with st.sidebar:
    st.header("Graph Control")
    
    if st.button("Graph Reload", use_container_width=True):
        st.rerun()
    
    st.divider()
    
    if st.button("Graph Delete", use_container_width=True):
        if st.checkbox("정말로 삭제하시겠습니까? (복구 불가)"):
            if reset_database():
                st.success("데이터베이스가 초기화되었습니다.")
                st.rerun()
    
    st.divider()

# --- 5. 그래프 렌더링 ---
nodes, edges = get_graph_data()

if not nodes:
    st.info("아직 저장된 지식이 없습니다. 1페이지에서 대화를 먼저 진행해 주세요!")
else:
    # 그래프 설정
    config_visual = Config(
        width=1200,
        height=800,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F59E0B",
        collapsible=False
    )
    
    st.write(f"현재 총 {len(nodes)}개의 지식 노드가 연결되어 있습니다.")
    
    # 그래프 출력
    agraph(nodes=nodes, edges=edges, config=config_visual)

    # 노드 상세 정보 표시
    st.info("info: 마우스로 노드를 드래그하거나 확대/축소할 수 있습니다.")