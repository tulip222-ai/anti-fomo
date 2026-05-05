#!/bin/bash
# 反 FOMO 后端启动脚本

echo "🚀 启动反 FOMO 后端服务..."

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 设置环境变量
export SECRET_KEY="${SECRET_KEY:-anti-fomo-secret-key-change-in-production}"
export FLASK_APP=app.py
export FLASK_ENV=production

# 启动服务
echo "📡 服务将在 http://0.0.0.0:5000 启动"
python3 app.py
