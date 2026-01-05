import sys
try:
    with open("app_streamlit.py", "r", encoding="utf-8") as f:
        compile(f.read(), "app_streamlit.py", "exec")
    print("Syntax OK")
except Exception as e:
    print(f"Syntax Error: {e}")
