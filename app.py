#!/usr/bin/env python3
"""
反 FOMO 后端服务
功能：用户认证、搜索数据统计、API 代理
"""

import os
import json
import sqlite3
import hashlib
import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import bcrypt

app = Flask(__name__, static_folder='static')
CORS(app)

# 配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'anti-fomo-secret-key-change-in-production')
DATABASE = 'anti_fomo.db'

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # 用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 搜索记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            user_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建默认管理员账户
    default_password = hashlib.sha256('admin123'.encode()).hexdigest()
    hashed = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt())
    try:
        c.execute('''
            INSERT OR IGNORE INTO users (username, password, is_admin)
            VALUES (?, ?, ?)
        ''', ('admin', hashed, 1))
    except:
        pass
    
    conn.commit()
    conn.close()

# 获取数据库连接
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# JWT 认证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token 格式错误'}), 401
        
        if not token:
            return jsonify({'message': '缺少认证 Token'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token 已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的 Token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if not current_user.get('is_admin'):
            return jsonify({'message': '需要管理员权限'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

# ==================== 认证接口 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    if len(username) < 3 or len(password) < 6:
        return jsonify({'message': '用户名至少3位，密码至少6位'}), 400
    
    # 密码哈希
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    hashed = bcrypt.hashpw(password_hash.encode(), bcrypt.gensalt())
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({'message': '注册成功'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': '用户名已存在'}), 409

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 验证密码
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if not bcrypt.checkpw(password_hash.encode(), user['password']):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 生成 JWT
    token = jwt.encode({
        'user_id': user['id'],
        'username': user['username'],
        'is_admin': bool(user['is_admin']),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'is_admin': bool(user['is_admin'])
        }
    })

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({'user': current_user})

# ==================== 搜索统计接口 ====================

@app.route('/api/search/log', methods=['POST'])
def log_search():
    """记录搜索请求"""
    data = request.get_json()
    term = data.get('term', '').strip().lower()
    
    if not term:
        return jsonify({'message': '搜索词不能为空'}), 400
    
    # 获取用户信息（如果已登录）
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded.get('user_id')
        except:
            pass
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO search_logs (term, user_id, ip_address, user_agent)
        VALUES (?, ?, ?, ?)
    ''', (term, user_id, request.remote_addr, request.headers.get('User-Agent')))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '记录成功'}), 201

@app.route('/api/search/stats', methods=['GET'])
@admin_required
def get_search_stats(current_user):
    """获取搜索统计（管理员）"""
    conn = get_db()
    c = conn.cursor()
    
    # 热门搜索词
    c.execute('''
        SELECT term, COUNT(*) as count
        FROM search_logs
        GROUP BY term
        ORDER BY count DESC
        LIMIT 20
    ''')
    hot_terms = [{'term': row['term'], 'count': row['count']} for row in c.fetchall()]
    
    # 总搜索次数
    c.execute('SELECT COUNT(*) as total FROM search_logs')
    total_searches = c.fetchone()['total']
    
    # 今日搜索次数
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT COUNT(*) as today_count
        FROM search_logs
        WHERE date(created_at) = date('now')
    ''')
    today_searches = c.fetchone()['today_count']
    
    # 独立搜索词数量
    c.execute('SELECT COUNT(DISTINCT term) as unique_terms FROM search_logs')
    unique_terms = c.fetchone()['unique_terms']
    
    # 最近搜索
    c.execute('''
        SELECT term, created_at
        FROM search_logs
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    recent_searches = [{'term': row['term'], 'time': row['created_at']} for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        'hot_terms': hot_terms,
        'total_searches': total_searches,
        'today_searches': today_searches,
        'unique_terms': unique_terms,
        'recent_searches': recent_searches
    })

@app.route('/api/search/history', methods=['GET'])
@token_required
def get_user_search_history(current_user):
    """获取用户个人搜索历史"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT term, created_at
        FROM search_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (current_user['user_id'],))
    history = [{'term': row['term'], 'time': row['created_at']} for row in c.fetchall()]
    conn.close()
    
    return jsonify({'history': history})

# ==================== 分析接口（代理到 AI API）====================

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析技术名词（需要登录）"""
    data = request.get_json()
    term = data.get('term', '').strip()
    
    if not term:
        return jsonify({'message': '技术名词不能为空'}), 400
    
    # 记录搜索
    conn = get_db()
    c = conn.cursor()
    
    # 获取用户信息
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded.get('user_id')
        except:
            pass
    
    c.execute('''
        INSERT INTO search_logs (term, user_id, ip_address, user_agent)
        VALUES (?, ?, ?, ?)
    ''', (term.lower(), user_id, request.remote_addr, request.headers.get('User-Agent')))
    conn.commit()
    conn.close()
    
    # 返回模拟数据（实际项目中这里调用 AI API）
    return jsonify(generate_mock_response(term))

def generate_mock_response(term):
    """生成模拟分析数据"""
    mock_data = {
        'mamba': {
            'verdict': 'yellow',
            'verdictReason': '长序列场景有优势，但通用能力尚未超越 Transformer',
            'firstPrinciples': 'Mamba 是一种选择性状态空间模型。输入是离散的 token 序列，输出是上下文相关的隐藏状态。核心变换是通过输入依赖的状态转移参数，让模型选择性关注重要信息，实现线性时间复杂度处理长序列。',
            'truth': '不是 Transformer 杀手，只是在特定长序列场景下的效率优化方案。',
            'hypeVsReality': [
                {'hype': 'Transformer 杀手，彻底颠覆 NLP', 'reality': '长序列场景有优势，但通用能力尚未超越'},
                {'hype': '线性复杂度解决所有效率问题', 'reality': '硬件优化和内存带宽仍是瓶颈'}
            ]
        },
        'gpt-4': {
            'verdict': 'green',
            'verdictReason': '当前最通用的多模态大模型，生产环境首选',
            'firstPrinciples': 'GPT-4 是基于 Transformer 架构的大型语言模型。输入是文本/图像 token 序列，输出是下一个 token 的概率预测。核心变换是通过海量数据预训练学习语言模式，再用强化学习对齐人类偏好。',
            'truth': '强大的模式匹配工具，但不是真正的智能，仍有幻觉问题。',
            'hypeVsReality': [
                {'hype': '完全理解人类意图，零错误', 'reality': '仍有幻觉问题，需要提示工程优化'},
                {'hype': '可以替代所有程序员', 'reality': '辅助编程能力强，但复杂架构设计仍需人工'}
            ]
        },
        'rag': {
            'verdict': 'green',
            'verdictReason': '检索增强生成是成熟架构模式',
            'firstPrinciples': 'RAG 将外部知识检索与大模型生成结合。输入是用户查询，系统先从知识库检索相关文档，再将检索结果与用户查询拼接送给大模型生成回答。',
            'truth': '不是万能药，检索质量决定生成质量，维护知识库需要持续投入。',
            'hypeVsReality': [
                {'hype': '完全消除模型幻觉', 'reality': '检索质量决定生成质量，仍可能产生错误'},
                {'hype': '无需微调就能解决所有领域问题', 'reality': '复杂领域仍需微调 + RAG 结合'}
            ]
        },
        'lora': {
            'verdict': 'green',
            'verdictReason': '高效微调的标准方案，生态完善',
            'firstPrinciples': 'LoRA 通过在预训练权重旁添加低秩矩阵来进行微调。核心变换是冻结原权重，只训练两个小型矩阵 A 和 B 的乘积来近似权重更新。',
            'truth': '不能替代全参数微调，复杂任务仍需全微调。',
            'hypeVsReality': [
                {'hype': '完全替代全参数微调', 'reality': '复杂任务仍需全微调'},
                {'hype': '训练成本几乎为零', 'reality': '仍需 GPU 资源，只是比全微调少'}
            ]
        }
    }
    
    lower_term = term.lower()
    for key, data in mock_data.items():
        if key in lower_term or lower_term in key:
            return {'term': term, **data}
    
    return {
        'term': term,
        'verdict': 'yellow',
        'verdictReason': '新兴技术概念，需要进一步观察其实际应用价值',
        'firstPrinciples': f'{term} 是一个 AI 相关技术。输入数据经过特定的算法处理，输出期望的结果。建议查阅官方文档获取更详细的技术细节。',
        'truth': '作为新兴概念，市场宣传可能夸大其实际能力，建议保持理性。',
        'hypeVsReality': [
            {'hype': '各种宣传中的神奇效果', 'reality': '实际效果需要具体场景验证'},
            {'hype': '立即改变行业格局', 'reality': '技术成熟度和生态建设需要时间'}
        ]
    }

# ==================== 静态文件服务 ====================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# 初始化数据库
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
