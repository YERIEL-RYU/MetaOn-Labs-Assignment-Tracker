import requests
from typing import List, Dict, Any
from crawler.base import BaseCrawler

class IrisCrawler(BaseCrawler):
    """
    IRIS (범부처통합연구지원시스템) 크롤러
    - API 엔드포인트 직접 호출 (requests 기반)
    """

    async def login(self, page: Any = None) -> bool:
        return True

    async def fetch_assignments(self, page: Any = None) -> List[Dict[str, Any]]:
        return []

    async def run(self) -> tuple[bool, str]:
        """Playwright 대신 가볍고 빠른 requests 기반 API 직접 호출로 오버라이드"""
        try:
            print(f"[{self.site_name}] IRIS API 호출 중...")
            url = "https://www.iris.go.kr/contents/retrieveBsnsAncmBtinSituList.do"
            
            # API에 필요한 파라미터 (접수중인 1페이지 목록)
            data = {
                "pageIndex": 1,
                "ancmPrg": "ancmIng"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=self.timeout / 1000)
            
            if response.status_code != 200:
                error_msg = f"HTTP Error {response.status_code}"
                print(f"[{self.site_name}] {error_msg}")
                return False, error_msg
                
            json_data = response.json()
            
            # IRIS 실제 JSON 응답 키인 'listBsnsAncmBtinSitu' 사용
            items = json_data.get('listBsnsAncmBtinSitu', [])
            
            assignments = []
            for item in items:
                status_text = item.get('rcveStt', '')
                status = 'pending'
                if '마감' in status_text or status_text == '종료':
                    status = 'missing'
                    
                assignments.append({
                    "course": item.get('sorgnNm', 'IRIS'),
                    "title": item.get('ancmTl', '공고명 없음'),
                    "deadline": self.normalize_deadline(item.get('rcveEndDe', '')),
                    "status": status,
                    "url": f"https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmNo={item.get('ancmNo', '')}",
                    "description": item.get('ancmNo', '')
                })
                
            if assignments:
                self.save(assignments)
                print(f"[{self.site_name}] {len(assignments)}개 과제 저장 완료.")
            else:
                print(f"[{self.site_name}] 수집된 과제가 없습니다.")
                
            return True, ""
            
        except Exception as e:
            error_msg = f"크롤링 중 오류 발생: {str(e)}"
            print(f"[{self.site_name}] {error_msg}")
            return False, error_msg

    # normalize_deadline은 BaseCrawler의 기본 구현 사용
