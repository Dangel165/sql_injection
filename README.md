# SecureBank - 온라인 뱅킹 시스템

안전하고 편리한 온라인 뱅킹 서비스입니다.

## 🏦 서비스 소개

SecureBank는 최신 보안 기술을 적용한 온라인 뱅킹 플랫폼입니다.
- 계좌 조회 및 관리
- 온라인 이체 서비스  
- 투자상품 안내
- 고객 지원 서비스

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

#### 문제점:
1. **문자열 연결**: 사용자 입력을 직접 SQL 쿼리 문자열에 연결
2. **입력 검증 부재**: 특수문자나 SQL 메타문자에 대한 필터링 없음
3. **이스케이프 처리 없음**: SQL 구문을 변경할 수 있는 문자들이 그대로 실행됨

### 🔓 SQL 인젝션 공격 방법

#### 1. 인증 우회 공격
```
사용자명: admin' OR '1'='1' --
비밀번호: (아무거나)
```

**실행되는 쿼리:**
```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1' --' AND password = '해시값'
```

**결과:** `'1'='1'`은 항상 참이므로 비밀번호 확인 없이 로그인 성공

#### 2. UNION 기반 공격
```
사용자명: ' UNION SELECT 1,2,3,4,5,6,7,8,9,10,11,12 --
비밀번호: (아무거나)
```

**결과:** 데이터베이스 구조 파악 및 추가 정보 추출 가능

#### 3. Boolean 기반 공격
```
사용자명: ' OR 1=1 --
비밀번호: (아무거나)
```

**결과:** 모든 사용자 정보에 접근 가능

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
