import streamlit as st

home_page = st.Page("./home.py", title="Home", default=True)
graphiti_page = st.Page("./1_Graphiti_Agent.py", title="Graphiti Agent")
visualization_page = st.Page("./2_Graph_Visualization.py", title="Graph Visualization")
comparison_page = st.Page("./3_Comparison_LangGraph.py", title="Comparison with LangGraph")

pg = st.navigation([home_page, graphiti_page, visualization_page, comparison_page])

pg.run()