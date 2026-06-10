# pyrefly: ignore [missing-import]
import streamlit as st
import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.handler import add_site, get_all_sites, update_site, delete_site
from scheduler import run_crawler_sync

st.title("➕ 사이트 등록")

# 자동 감지된 크롤러 클래스 목록 (간단히 하드코딩 또는 폴더 스캔)
# 실제로는 crawler 폴더를 뒤져서 BaseCrawler를 상속받은 클래스를 찾을 수 있음
AVAILABLE_CRAWLERS = [
    "CoursemosCrawler", "LcmsCrawler", 
    "SromeCrawler", "NtisCrawler", "IrisCrawler", "HtdreamCrawler"
]

with st.form("add_site_form"):
    st.subheader("새로운 LMS/과제 사이트 정보 입력")
    
    name = st.text_input("사이트명 (예: 코스모스 대학교)")
    url = st.text_input("홈페이지 URL (예: https://lms.univ.ac.kr)")
    login_url = st.text_input("로그인 URL (로그인이 필요없는 사이트라면 비워두세요)")
    
    c1, c2 = st.columns(2)
    with c1:
        username = st.text_input("아이디 (선택)")
    with c2:
        password = st.text_input("비밀번호 (선택)", type="password")
        
    crawler_help = """
    **크롤러 타입 안내:**
    - `CoursemosCrawler`: 코스모스(Coursemos) 기반 대학/기관 LMS용 크롤러입니다.
    - `LcmsCrawler`: 일반적인 LCMS 환경용 크롤러입니다.
    - `SromeCrawler`: S-ROME (KEIT 산업기술R&D) 공고 수집 (requests 방식, 로그인 불필요)
    - `NtisCrawler`: NTIS (국가R&D통합공고) 수집 (Playwright, User-Agent 우회 적용)
    - `IrisCrawler`: IRIS (범부처통합연구지원시스템) 수집 (Playwright, XHR JSON 인터셉트 적용)
    - `HtdreamCrawler`: 보건의료기술종합정보시스템 수집 (Playwright, .env 로그인 연동)
    
    ※ 맞춤형 파싱 로직이 필요한 경우, `crawler` 폴더에 새로운 크롤러 클래스를 추가하고 등록할 수 있습니다.
    """
    crawler_class = st.selectbox("크롤러 타입", AVAILABLE_CRAWLERS, help=crawler_help)
    
    submitted = st.form_submit_button("등록 및 저장")
    
    if submitted:
        if name and url:
            add_site(name, url, login_url, username, password, crawler_class)
            st.success(f"'{name}' 사이트가 성공적으로 등록되었습니다.")
            st.balloons()
        else:
            st.error("사이트명과 홈페이지 URL은 필수 입력 항목입니다.")

@st.dialog("사이트 수정")
def edit_site_dialog(site):
    with st.form(f"edit_form_{site['id']}"):
        new_name = st.text_input("사이트명", value=site['name'])
        new_url = st.text_input("홈페이지 URL", value=site['url'])
        new_login_url = st.text_input("로그인 URL", value=site['login_url'])
        
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("아이디 (선택)", value=site['username'])
        with c2:
            new_password = st.text_input("비밀번호 (선택)", type="password", value=site['password'])
            
        try:
            default_idx = AVAILABLE_CRAWLERS.index(site['crawler_class'])
        except ValueError:
            default_idx = 0
            
        new_crawler = st.selectbox("크롤러 타입", AVAILABLE_CRAWLERS, index=default_idx)
        new_active = st.checkbox("자동 크롤링 활성화", value=bool(site['active']))
        
        if st.form_submit_button("저장"):
            if new_name and new_url:
                update_site(site['id'], new_name, new_url, new_login_url, new_username, new_password, new_crawler, new_active)
                st.rerun()
            else:
                st.error("사이트명과 URL은 필수입니다.")

st.markdown("---")
st.subheader("등록된 사이트 목록")
sites = get_all_sites()

if sites:
    for site in sites:
        with st.expander(f"{site['name']} ({'활성' if site['active'] else '비활성'})"):
            st.write(f"- **URL**: {site['url']}")
            st.write(f"- **아이디**: {site['username']}")
            st.write(f"- **크롤러**: {site['crawler_class']}")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("▶️ 연결 테스트", key=f"test_{site['id']}", use_container_width=True):
                    with st.spinner("로그인 및 크롤링 테스트 중..."):
                        run_crawler_sync(site)
                    st.toast("테스트가 완료되었습니다. 대시보드 및 로그를 확인하세요.", icon="✅")
            with c2:
                if st.button("✏️ 수정", key=f"edit_{site['id']}", use_container_width=True):
                    edit_site_dialog(site)
            with c3:
                if st.button("🗑️ 삭제", key=f"del_{site['id']}", type="primary", use_container_width=True):
                    delete_site(site['id'])
                    st.toast(f"'{site['name']}' 사이트가 삭제되었습니다.", icon="✅")
                    st.rerun()
else:
    st.info("아직 등록된 사이트가 없습니다.")
