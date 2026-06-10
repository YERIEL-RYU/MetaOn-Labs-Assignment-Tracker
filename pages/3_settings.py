import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.handler import get_crawl_logs
from scheduler import update_scheduler_interval

st.title("⚙️ 설정 및 로그")

st.header("크롤링 설정")
# 세션 스테이트나 DB에 저장하면 좋지만, 이번에는 데모 목적으로 세션에만 유지
if "crawl_interval" not in st.session_state:
    st.session_state.crawl_interval = 720

col1, col2 = st.columns(2)
with col1:
    interval_options = {
        24: "하루",
        72: "3일",
        120: "5일",
        168: "일주일",
        720: "한달"
    }
    
    current_interval = st.session_state.crawl_interval
    if current_interval not in interval_options:
        current_interval = 720
        st.session_state.crawl_interval = 720

    interval = st.selectbox(
        "자동 크롤링 주기", 
        list(interval_options.keys()), 
        index=list(interval_options.keys()).index(current_interval),
        format_func=lambda x: interval_options[x]
    )
    
    if st.button("주기 변경 적용"):
        st.session_state.crawl_interval = interval
        update_scheduler_interval(interval)
        st.success(f"크롤링 주기가 '{interval_options[interval]}' 단위로 변경되었습니다.")

with col2:
    noti_days = st.number_input("마감 임박 알림 기준일", min_value=1, max_value=7, value=3)
    st.caption("대시보드에서 '마감 임박'으로 표시될 기준일입니다.")

st.markdown("---")

st.header("📝 최근 크롤링 로그")
logs = get_crawl_logs(limit=20)

if logs:
    log_df = pd.DataFrame(logs)
    # 컬럼 포맷팅
    log_df['started_at'] = pd.to_datetime(log_df['started_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    log_df['finished_at'] = pd.to_datetime(log_df['finished_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    log_df['success'] = log_df['success'].apply(lambda x: "✅ 성공" if x else "❌ 실패")
    
    # 열 이름 변경
    log_df.rename(columns={
        'site_name': '사이트명',
        'started_at': '시작 시간',
        'finished_at': '종료 시간',
        'success': '결과',
        'error_msg': '에러 메시지'
    }, inplace=True)
    
    st.dataframe(
        log_df[['사이트명', '시작 시간', '종료 시간', '결과', '에러 메시지']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("아직 기록된 크롤링 로그가 없습니다.")
