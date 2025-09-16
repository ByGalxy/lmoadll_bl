# 示例

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, request, session, redirect, render_template

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 务必设置一个安全的密钥

# 创建PasswordHasher实例（可自定义参数）
ph = PasswordHasher(
    time_cost=2,      # 迭代次数，推荐2-4:cite[5]
    memory_cost=102400,  # 内存开销（单位KB，如100MB）
    parallelism=2,    # 并行线程数
    hash_len=32,      # 输出哈希长度（字节）
    salt_len=16       # 盐值长度（字节）
)

def hash_password(password):
    """对密码进行哈希处理"""
    try:
        pw_hash = ph.hash(password)
        return pw_hash
    except Exception as e:
        print(f"哈希处理失败: {e}")
        return None

def verify_password(pw_hash, password):
    """验证密码是否匹配哈希值"""
    try:
        return ph.verify(pw_hash, password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        return False

# 示例Flask路由
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    pw_hash = hash_password(password)
    if pw_hash:
        # 将用户名和pw_hash存储到数据库
        return "注册成功！"
    else:
        return "注册失败，请重试。"

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # 从数据库根据用户名检索存储的哈希值
    stored_hash = get_password_hash_from_db(username)  # 需自行实现
    if stored_hash and verify_password(stored_hash, password):
        session['username'] = username
        return redirect('/dashboard')
    else:
        return "用户名或密码错误。"