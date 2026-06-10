import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.handler import get_assignments, get_all_sites, update_assignment_status
from scheduler import run_crawler_sync

st.title("📊 과제 대시보드")

# 1. 사이트 목록 가져오기 (필터 및 수동 크롤링 용)
sites = get_all_sites()
site_dict = {site['id']: site['name'] for site in sites}

# 2. 상단 액션 (수동 크롤링)
cols = st.columns([3, 1])
with cols[1]:
    if st.button("🔄 즉시 크롤링 (모두)"):
        with st.spinner("크롤링 진행 중..."):
            for site in sites:
                if site['active']:
                    run_crawler_sync(site)
        st.toast("크롤링이 완료되었습니다!", icon="✅")
        st.rerun()

# 3. 데이터 로드 및 전처리
assignments = get_assignments()
df = pd.DataFrame(assignments)

if not df.empty:
    df['deadline'] = pd.to_datetime(df['deadline'], errors='coerce')
    now = datetime.now()
    
    # 메트릭 계산
    total = len(df)
    missing = len(df[(df['status'] != 'submitted') & (df['deadline'] < now)])
    
    # 마감 3일 이내 (미제출 상태만)
    soon_mask = (df['status'] != 'submitted') & (df['deadline'] >= now) & (df['deadline'] <= now + timedelta(days=3))
    soon = len(df[soon_mask])
    
    done = len(df[df['status'] == 'submitted'])

    # 4. 메트릭 카드
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체 과제", total)
    m2.metric("마감 지남 (미제출)", missing, delta_color="inverse")
    m3.metric("마감 임박 (3일 이내)", soon, delta_color="inverse")
    m4.metric("제출 완료", done)

    # 알림 표시 (풍선 효과)
    if soon > 0:
        st.toast(f"마감 3일 이내인 과제가 {soon}개 있습니다!", icon="🚨")
        # st.balloons() # 필요시 활성화

    st.markdown("---")

    status_map = {
        "pending": "미제출",
        "submitted": "제출완료",
        "missing": "마감지남"
    }

    # 5. 필터
    f1, f2, f3 = st.columns(3, vertical_alignment="bottom")
    with f1:
        sel_site = st.selectbox("사이트 필터", ["전체"] + list(site_dict.values()))
    with f2:
        sel_status = st.selectbox(
            "상태 필터", 
            ["전체", "pending", "submitted", "missing"],
            format_func=lambda x: "전체" if x == "전체" else status_map.get(x, x)
        )
    with f3:
        sel_soon = st.checkbox("마감 임박(3일)만 보기")

    # 필터 적용
    filtered_df = df.copy()
    if sel_site != "전체":
        filtered_df = filtered_df[filtered_df['site_name'] == sel_site]
    if sel_status != "전체":
        filtered_df = filtered_df[filtered_df['status'] == sel_status]
    if sel_soon:
        filtered_df = filtered_df[soon_mask]

    # 6. 테이블 출력
    st.subheader("📋 과제 목록")
    
    for idx, row in filtered_df.iterrows():
        deadline_str = "미정"
        d_day_str = ""
        
        if pd.notnull(row['deadline']):
            dt = row['deadline']
            # 날짜만 비교하기 위해 date() 사용
            diff = dt.date() - now.date()
            days = diff.days
            
            if days < 0:
                d_day_str = "🛑 [마감 지남]"
            elif days == 0:
                d_day_str = "🔥 [D-Day]"
            else:
                d_day_str = f"⏳ [D-{days}]"
                
            deadline_str = f"{dt.strftime('%Y.%m.%d %H:%M')}"

        header_title = f"[{row['site_name']}] {row['course']} - {row['title']}"
        header_time = f"{d_day_str} {deadline_str}" if d_day_str else f"마감: {deadline_str}"
        
        col_main, col_time = st.columns([4, 1], vertical_alignment="center")
        with col_time:
            st.markdown(f"<div style='text-align: right;'>{header_time}</div>", unsafe_allow_html=True)
            
        with col_main:
            with st.expander(header_title):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**상태:** {status_map.get(row['status'], row['status'])}")
                    if row['url']:
                        st.markdown(f"[바로가기]({row['url']})")
                    if row['description']:
                        st.write(row['description'])
                with c2:
                    # 상태 변경 버튼
                    new_status = st.selectbox(
                        "상태 변경", 
                        options=["pending", "submitted", "missing"], 
                        index=["pending", "submitted", "missing"].index(row['status']),
                        format_func=lambda x: status_map.get(x, x),
                        key=f"status_{row['id']}"
                    )
                    if new_status != row['status']:
                        update_assignment_status(row['id'], new_status)
                        st.toast("상태가 업데이트되었습니다.", icon="✅")
                        st.rerun()

else:
    st.info("등록된 과제가 없습니다. 사이트를 추가하고 크롤링을 실행해 보세요.")
