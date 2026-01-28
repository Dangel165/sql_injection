from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 데이터베이스 초기화
def init_db():
    import os
    if os.path.exists('users.db'):
        os.remove('users.db')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 사용자 테이블 생성
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            full_name TEXT,
            phone TEXT,
            address TEXT,
            account_balance INTEGER DEFAULT 0,
            account_status TEXT DEFAULT 'active',
            created_date TEXT,
            last_login TEXT
        )
    ''')
    
    # 거래 내역 테이블 생성
    cursor.execute('''
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_type TEXT,
            amount INTEGER,
            description TEXT,
            transaction_date TEXT,
            balance_after INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 로그 테이블 생성
    cursor.execute('''
        CREATE TABLE system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            ip_address TEXT,
            timestamp TEXT,
            details TEXT
        )
    ''')
    
    # 기본 사용자 추가
    users = [
        ('admin', 'admin123', 'admin@securebank.com', 'admin', '김관리', '02-1234-5678', '서울시 강남구 테헤란로 123', 50000000, 'active', '2024-01-01', '2024-01-29'),
        ('user1', 'password123', 'user1@gmail.com', 'user', '이철수', '010-1234-5678', '서울시 서초구 서초대로 456', 2450000, 'active', '2024-01-15', '2024-01-29'),
        ('user2', 'mypassword', 'user2@naver.com', 'user', '박영희', '010-9876-5432', '부산시 해운대구 해운대로 789', 1850000, 'active', '2024-01-20', '2024-01-28'),
        ('guest', 'guest', 'guest@securebank.com', 'guest', '방문자', '02-0000-0000', '임시 주소', 100000, 'limited', '2024-01-29', '2024-01-29'),
        ('john_doe', 'john2024', 'john@company.com', 'user', '존 도우', '010-5555-1234', '경기도 성남시 분당구 정자로 100', 5200000, 'active', '2024-01-10', '2024-01-28'),
        ('sarah_kim', 'sarah123', 'sarah@business.co.kr', 'user', '김사라', '010-7777-8888', '인천시 연수구 송도대로 200', 3300000, 'active', '2024-01-12', '2024-01-27')
    ]
    
    for username, password, email, role, full_name, phone, address, balance, status, created, last_login in users:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, email, role, full_name, phone, address, account_balance, account_status, created_date, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (username, hashed_password, email, role, full_name, phone, address, balance, status, created, last_login)
        )
    
    # 샘플 거래 내역 추가
    transactions = [
        (2, 'deposit', 3200000, '급여 입금', '2024-01-28', 2450000),
        (2, 'withdraw', -45000, '온라인 쇼핑몰', '2024-01-29', 2405000),
        (2, 'withdraw', -8500, '카페 결제', '2024-01-27', 2441500),
        (3, 'deposit', 2000000, '사업 수익', '2024-01-25', 1850000),
        (3, 'withdraw', -150000, '공과금 납부', '2024-01-26', 1700000),
        (5, 'deposit', 4500000, '프로젝트 대금', '2024-01-20', 5200000),
        (5, 'withdraw', -300000, '투자상품 구매', '2024-01-22', 4900000),
        (6, 'deposit', 2800000, '컨설팅 수익', '2024-01-18', 3300000),
        (6, 'withdraw', -500000, '부동산 투자', '2024-01-24', 2800000)
    ]
    
    for user_id, t_type, amount, desc, date, balance in transactions:
        cursor.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description, transaction_date, balance_after) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, t_type, amount, desc, date, balance)
        )
    
    # 시스템 로그 추가
    logs = [
        (1, 'admin_login', '192.168.1.100', '2024-01-29 09:30:00', '관리자 로그인'),
        (2, 'user_login', '192.168.1.101', '2024-01-29 10:15:00', '사용자 로그인'),
        (1, 'view_users', '192.168.1.100', '2024-01-29 09:35:00', '전체 사용자 조회'),
        (3, 'user_login', '192.168.1.102', '2024-01-28 14:20:00', '사용자 로그인'),
        (1, 'system_backup', '192.168.1.100', '2024-01-29 02:00:00', '시스템 백업 실행')
    ]
    
    for user_id, action, ip, timestamp, details in logs:
        cursor.execute(
            "INSERT INTO system_logs (user_id, action, ip_address, timestamp, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, ip, timestamp, details)
        )
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

# 취약한 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # 취약한 SQL 쿼리
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashlib.sha256(password.encode()).hexdigest()}'"
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
                
                # 로그인 로그 기록 (같은 연결 사용)
                try:
                    log_query = f"INSERT INTO system_logs (user_id, action, ip_address, timestamp, details) VALUES ({user[0]}, 'login', '{request.remote_addr}', '2024-01-29 10:00:00', '{user[1]} 로그인')"
                    cursor.execute(log_query)
                    conn.commit()
                except:
                    pass  # 로그 실패해도 로그인은 진행
                
                flash(f'환영합니다, {user[5] or user[1]}님!', 'success')
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                flash('아이디 또는 비밀번호가 잘못되었습니다.', 'error')
        except Exception as e:
            flash('로그인 중 오류가 발생했습니다.', 'error')
        finally:
            conn.close()
    
    return render_template('login.html')

# 안전한 로그인 (매개변수화된 쿼리 사용)
@app.route('/secure_login', methods=['GET', 'POST'])
def secure_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # 안전한 쿼리 - 매개변수화된 쿼리 사용
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            flash(f'환영합니다, {user[1]}님!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('아이디 또는 비밀번호가 잘못되었습니다.', 'error')
        
        conn.close()
    
    return render_template('secure_login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    conn.execute('PRAGMA journal_mode=WAL')  # WAL 모드로 설정
    cursor = conn.cursor()
    
    # 사용자 정보 조회
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    # 최근 거래 내역 조회
    cursor.execute("""
        SELECT transaction_type, amount, description, transaction_date, balance_after 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY transaction_date DESC 
        LIMIT 5
    """, (session['user_id'],))
    recent_transactions = cursor.fetchall()
    
    conn.close()
    
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    return render_template('dashboard.html', user=user, transactions=recent_transactions)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    conn.execute('PRAGMA journal_mode=WAL')  # WAL 모드로 설정
    cursor = conn.cursor()
    
    # 전체 통계
    cursor.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    total_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE account_status = 'active'")
    active_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(account_balance) FROM users WHERE role != 'admin'")
    total_deposits = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE transaction_date = '2024-01-29'")
    today_transactions = cursor.fetchone()[0]
    
    # 모든 고객 정보
    cursor.execute("""
        SELECT id, username, full_name, email, phone, account_balance, 
               account_status, created_date, last_login 
        FROM users 
        WHERE role != 'admin' 
        ORDER BY created_date DESC
    """)
    all_customers = cursor.fetchall()
    
    # 최근 거래 내역
    cursor.execute("""
        SELECT t.id, u.username, u.full_name, t.transaction_type, t.amount, 
               t.description, t.transaction_date, t.balance_after
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.transaction_date DESC
        LIMIT 10
    """)
    recent_transactions = cursor.fetchall()
    
    # 시스템 로그
    cursor.execute("""
        SELECT l.id, u.username, l.action, l.ip_address, l.timestamp, l.details
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.timestamp DESC
        LIMIT 15
    """)
    system_logs = cursor.fetchall()
    
    # 계정 상태별 통계
    cursor.execute("""
        SELECT account_status, COUNT(*) 
        FROM users 
        WHERE role != 'admin' 
        GROUP BY account_status
    """)
    status_stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_customers=total_customers,
                         active_customers=active_customers,
                         total_deposits=total_deposits,
                         today_transactions=today_transactions,
                         customers=all_customers,
                         transactions=recent_transactions,
                         logs=system_logs,
                         status_stats=status_stats)

@app.route('/admin/customer/<int:customer_id>')
def customer_detail(customer_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    # 고객 정보
    cursor.execute("SELECT * FROM users WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('고객을 찾을 수 없습니다.', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    # 고객 거래 내역
    cursor.execute("""
        SELECT transaction_type, amount, description, transaction_date, balance_after
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY transaction_date DESC
    """, (customer_id,))
    transactions = cursor.fetchall()
    
    conn.close()
    
    return render_template('customer_detail.html', customer=customer, transactions=transactions)

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('users.db')
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    
    # 월별 가입자 통계
    cursor.execute("""
        SELECT strftime('%Y-%m', created_date) as month, COUNT(*) as count
        FROM users 
        WHERE role != 'admin'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    monthly_signups = cursor.fetchall()
    
    # 거래 유형별 통계
    cursor.execute("""
        SELECT transaction_type, COUNT(*) as count, SUM(ABS(amount)) as total_amount
        FROM transactions
        GROUP BY transaction_type
    """)
    transaction_stats = cursor.fetchall()
    
    # 잔액 구간별 고객 분포
    cursor.execute("""
        SELECT 
            CASE 
                WHEN account_balance < 1000000 THEN '100만원 미만'
                WHEN account_balance < 5000000 THEN '100만원-500만원'
                WHEN account_balance < 10000000 THEN '500만원-1000만원'
                ELSE '1000만원 이상'
            END as balance_range,
            COUNT(*) as count
        FROM users 
        WHERE role != 'admin'
        GROUP BY balance_range
    """)
    balance_distribution = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_reports.html',
                         monthly_signups=monthly_signups,
                         transaction_stats=transaction_stats,
                         balance_distribution=balance_distribution)

@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()

    app.run(debug=True, host='0.0.0.0', port=5000)
