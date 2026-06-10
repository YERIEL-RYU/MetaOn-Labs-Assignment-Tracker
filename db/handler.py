import sqlite3
import os
import base64
import datetime

DB_PATH = 'assignment.db'
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.commit()

def encode_pw(password: str) -> str:
    """간단한 비밀번호 인코딩 (프로토타입용)"""
    return base64.b64encode(password.encode('utf-8')).decode('utf-8')

def decode_pw(encoded: str) -> str:
    """간단한 비밀번호 디코딩"""
    return base64.b64decode(encoded.encode('utf-8')).decode('utf-8')

def add_site(name, url, login_url, username, password, crawler_class):
    """사이트 정보 등록"""
    enc_pw = encode_pw(password)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sites (name, url, login_url, username, password, crawler_class)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, url, login_url, username, enc_pw, crawler_class))
        conn.commit()

def get_all_sites(active_only=False):
    """모든 사이트 조회"""
    query = "SELECT * FROM sites"
    if active_only:
        query += " WHERE active = 1"
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 비밀번호 복호화해서 반환
        sites = []
        for row in rows:
            site = dict(row)
            site['password'] = decode_pw(site['password'])
            sites.append(site)
        return sites

def update_site_status(site_id, active):
    """사이트 활성화 상태 변경"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE sites SET active = ? WHERE id = ?', (active, site_id))
        conn.commit()

def update_site(site_id, name, url, login_url, username, password, crawler_class, active):
    """사이트 정보 및 활성화 상태 전체 업데이트"""
    enc_pw = encode_pw(password) if password else ""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sites 
            SET name=?, url=?, login_url=?, username=?, password=?, crawler_class=?, active=?
            WHERE id=?
        ''', (name, url, login_url, username, enc_pw, crawler_class, int(active), site_id))
        conn.commit()

def delete_site(site_id):
    """사이트 및 연관 데이터(ON DELETE CASCADE) 삭제"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sites WHERE id = ?', (site_id,))
        conn.commit()

def save_assignments(site_id, assignments_data):
    """크롤링된 과제 정보 저장 및 업데이트"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for hw in assignments_data:
            cursor.execute('''
                INSERT INTO assignments (site_id, course, title, deadline, status, url, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(site_id, course, title) DO UPDATE SET
                deadline = excluded.deadline,
                url = excluded.url,
                description = excluded.description,
                status = CASE 
                            WHEN excluded.status = 'submitted' THEN 'submitted' 
                            ELSE assignments.status 
                         END,
                crawled_at = CURRENT_TIMESTAMP
            ''', (site_id, hw['course'], hw['title'], hw['deadline'], hw['status'], hw.get('url'), hw.get('description')))
        conn.commit()

def cleanup_old_assignments():
    """마감일이 2주(14일) 이상 지난 과제를 자동 삭제"""
    cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assignments WHERE deadline < ?", (cutoff_date,))
        conn.commit()

def get_assignments(filters=None):
    """조건에 맞는 과제 목록 조회"""
    cleanup_old_assignments()  # 2주 이상 지난 과제 자동 삭제
    
    query = "SELECT a.*, s.name as site_name FROM assignments a JOIN sites s ON a.site_id = s.id WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('site_id'):
            query += " AND a.site_id = ?"
            params.append(filters['site_id'])
        if filters.get('status'):
            query += " AND a.status = ?"
            params.append(filters['status'])
            
    query += " ORDER BY a.deadline ASC"
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def update_assignment_status(assignment_id, status):
    """과제 상태(제출 여부) 수동 변경"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE assignments SET status = ? WHERE id = ?', (status, assignment_id))
        conn.commit()

def add_crawl_log(site_id, started_at, finished_at, success, error_msg=""):
    """크롤링 결과 로그 추가"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crawl_logs (site_id, started_at, finished_at, success, error_msg)
            VALUES (?, ?, ?, ?, ?)
        ''', (site_id, started_at, finished_at, success, error_msg))
        conn.commit()

def get_crawl_logs(limit=20):
    """최근 크롤링 로그 조회"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.name as site_name 
            FROM crawl_logs c 
            JOIN sites s ON c.site_id = s.id 
            ORDER BY c.started_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
