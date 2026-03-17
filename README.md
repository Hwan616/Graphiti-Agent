# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. create virtual environment in Visual Studio Code
   ```
   $ python -m venv .venv
   ```

2. set virtual envrionment

   ```
   $ source .venv/bin/activate
   ```

3. write configs in .venv/config.json
   (1) create config.json file in .venv folder
   (2) wirte your configs
   ```
   {
      "OPENAI_API_KEY": "sk-proj-xxxxxxxxxxxx",
      "NEO4J_URI": "neo4j+s://xxxxxxxx.databases.neo4j.io",
      "NEO4J_USER": "neo4j",
      "NEO4J_PASSWORD": "your-password-here"
   }
   ```

3. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

4. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
