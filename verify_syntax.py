import sys
import traceback

try:
    with open("app_streamlit.py", "r", encoding="utf-8") as f:
        content = f.read()
    compile(content, "app_streamlit.py", "exec")
    with open("syntax_result.txt", "w", encoding="utf-8") as f:
        f.write("OK")
except Exception:
    with open("syntax_result.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
