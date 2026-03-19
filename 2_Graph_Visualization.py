import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase

st.set_page_config(page_title="Graph Visualization", layout="wide")
st.title("Graph Visualization")

# --- 1. 세션 검증 ---
if not st.session_state.get("config_loaded"):
    st.error("초기 설정이 로드되지 않았습니다.")
    if st.button("Home으로 이동"):
        st.switch_page("streamlit_app.py")
    st.stop()

# --- 2. Neo4j 드라이버 초기화 ---
config = st.session_state.neo4j_config
driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["user"], config["password"])
        )

# --- 3. 그래프 시각화 ---
with st.sidebar:
    st.header("Graph Visualization Settings")

    # Relationship Limit
    limit = st.number_input(
        label="Relationships Limit", 
        min_value=1,      # 최소값
        max_value=1000,   # 최대값
        value=30,         # 기본값
        step=1            # 증감 단위
    )
    st.caption("Relationship은 최근에 생성된 순으로 표시됩니다.")

    create_button = st.button("Create")

    st.divider()
    delete_button = st.button("Delete")
    confirm_delete = st.checkbox("그래프 삭제에 동의합니다.")

if create_button:
    try:
        query = f"MATCH (a)-[r]->(b) RETURN a, type(r) AS r, b ORDER BY a.createdAt DESC LIMIT {limit}"
        
        with driver.session() as session:
            result = session.run(query)
            records = list(result)

        if not records:
            st.info("데이터가 없습니다. Agent와 대화를 나누어 그래프를 생성하세요.")
        else:
            net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
            
            # Physics 설정 (그래프가 너무 흔들리지 않게)
            net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100)

            for record in records:
                node_a = record["a"]
                node_b = record["b"]
                rel_type = record["r"]

                # Node Label 추출 (name 속성 우선, 없으면 ID)
                def get_label(node):
                    return node.get("name", node.get("id", str(node.id)))

                a_id = str(node_a.id)
                b_id = str(node_b.id)
                a_label = get_label(node_a)
                b_label = get_label(node_b)

                net.add_node(a_id, label=a_label, title=str(dict(node_a)), color="#97C2FC")
                net.add_node(b_id, label=b_label, title=str(dict(node_b)), color="#FFFF00")
                net.add_edge(a_id, b_id, label=rel_type)

            # HTML 저장 및 표시
            net.save_graph("graph.html")
            with open("graph.html", "r", encoding="utf-8") as f:
                source = f.read()
            components.html(source, height=620)
            
    except Exception as e:
        st.error(f"시각화 오류: {e}")

if delete_button:
    if confirm_delete:
        try:
            # 1. Neo4j 데이터 삭제
            delete_query = "MATCH (n) DETACH DELETE n"
            with driver.session() as session:
                session.run(delete_query)
            # 2. Streamlit 세션 대화 기록 삭제
            st.session_state.messages = []

            st.sidebar.success("초기화 완료")
            st.rerun() # 화면 갱신
        except Exception as e:
            st.error(f"초기화 중 에러 발생: {e}")
    else:
        st.sidebar.warning("먼저 삭제 동의 체크박스를 선택해주세요.")