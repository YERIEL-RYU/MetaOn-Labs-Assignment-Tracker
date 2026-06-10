# Assignment Tracker 📚

과제 자동 수집 및 관리를 위한 Streamlit 기반 독립형 앱입니다. 
외부 에이전트 없이 로컬 환경에서 Playwright와 APScheduler를 이용해 백그라운드로 LMS 과제를 크롤링하여 대시보드에서 일괄 관리할 수 있습니다.

## 기능
- **다중 LMS 사이트 지원**: Coursemos, LCMS 등 다양한 시스템 크롤러 추가 가능
- **대시보드**: 전체 미제출, 마감 3일 이내, 제출 완료 과제를 시각적으로 확인
- **백그라운드 스케줄링**: 1시간, 3시간, 6시간 등 지정된 주기로 자동 크롤링 수행
- **로컬 데이터베이스**: SQLite를 이용해 모든 정보를 로컬 파일(`assignment.db`)에 안전하게 저장

## 설치 방법

```bash
# 1. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # (Windows 사용자의 경우: venv\Scripts\activate)

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Playwright 브라우저 엔진 설치 (최초 1회 필수)
playwright install chromium
```

## 실행 방법

```bash
# 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

## 크롤러 추가 방법
1. `crawler/base.py`의 `BaseCrawler`를 상속받는 새로운 클래스를 `crawler/` 디렉토리에 생성합니다.
2. `login(page)` 메서드와 `fetch_assignments(page)` 메서드를 구현하여 해당 사이트의 DOM 요소(CSS Selector)를 파싱합니다.
3. 앱을 재시작하고 "사이트 등록" 페이지에서 새로 만든 크롤러 타입을 선택하여 사이트를 추가합니다.

## 주의 사항
- `playwright`는 백그라운드 환경이나 서버 배포 시 종속성 패키지(예: 리눅스의 경우 `playwright install-deps`)가 필요할 수 있습니다.
- 보안을 위해 현재 비밀번호는 단순 base64 인코딩을 사용하여 SQLite에 저장됩니다. (프로토타입 버전) 상용 배포 시 강력한 암호화를 적용하시기 바랍니다.
- 크롤링 중인 대상 사이트의 구조가 변경되면 크롤러의 CSS 셀렉터를 수정해야 합니다.
