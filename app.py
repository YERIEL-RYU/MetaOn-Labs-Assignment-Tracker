import streamlit as st
import os
import sys

# 프로젝트 루트 경로를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.handler import init_db
from scheduler import start_scheduler

# 페이지 설정
st.set_page_config(
    page_title="과제 자동 수집 및 관리 앱",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화 (DB 및 스케줄러)
if "initialized" not in st.session_state:
    init_db()
    start_scheduler()
    st.session_state.initialized = True

# 멀티페이지 네비게이션 설정 (Streamlit >= 1.36)
pages = {
    "메뉴": [
        st.Page("pages/1_dashboard.py", title="대시보드", icon="📊", default=True),
        st.Page("pages/2_add_site.py", title="사이트 등록", icon="➕"),
        st.Page("pages/3_settings.py", title="설정", icon="⚙️"),
    ]
}

pg = st.navigation(pages)
pg.run()
