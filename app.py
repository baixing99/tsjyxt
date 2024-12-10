from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

# 设置 Flask 的密钥
app.secret_key = 'your_secret_key'

# 数据库连接
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row  # 允许列名作为字典访问
    return conn

# 创建数据库和表格（如果没有的话）
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建图书表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            quantity INTEGER
        )
    ''')

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    # 创建借阅记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            borrow_date DATE,
            return_date DATE,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')

    conn.commit()
    conn.close()

# 注册用户
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username =? AND password =?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            # 登录成功，将用户信息存储在会话中
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return "登录失败，请检查用户名和密码"
    return render_template('login.html')

# 用户登出
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # 删除会话中的用户信息
    return redirect(url_for('login'))  # 跳转到登录页面

# 首页
@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        conn.close()
        return render_template('index.html', books=books)
    else:
        return redirect(url_for('login'))  # 如果没有登录，跳转到登录页面

# 添加图书
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            author = request.form['author']
            quantity = request.form['quantity']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
                           (title, author, quantity))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        return render_template('add_book.html')
    else:
        return redirect(url_for('login'))

# 借阅图书
@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow(book_id):
    if 'user_id' in session:
        user_id = session['user_id']
        borrow_date = request.form['borrow_date']
        return_date = request.form['return_date']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM books WHERE id =?", (book_id,))
        book = cursor.fetchone()
        if book and book['quantity'] > 0:
            # 减少图书数量并添加借阅记录
            cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id =?", (book_id,))
            cursor.execute("INSERT INTO borrowings (user_id, book_id, borrow_date, return_date) VALUES (?, ?, ?, ?)",
                           (user_id, book_id, borrow_date, return_date))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            conn.close()
            return "该书已无库存"
    else:
        return redirect(url_for('login'))

# 归还图书
@app.route('/return/<int:borrowing_id>', methods=['POST'])
def return_book(borrowing_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT book_id FROM borrowings WHERE id =?", (borrowing_id,))
        book_id = cursor.fetchone()[0]
        cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id =?", (book_id,))
        cursor.execute("DELETE FROM borrowings WHERE id =?", (borrowing_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()  # 初始化数据库
    app.run(debug=True)
