#!/bin/bash
# 一键部署到 Railway

echo "🚀 开始部署到 Railway..."

# 检查是否安装了 railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 安装 Railway CLI..."
    npm install -g @railway/cli
fi

# 登录 Railway
echo "🔑 请登录 Railway..."
railway login

# 初始化项目（如果没有）
if [ ! -f .railway/config.json ]; then
    echo "📁 初始化 Railway 项目..."
    railway init
fi

# 设置环境变量
echo "⚙️ 设置环境变量..."
read -p "请输入 SECRET_KEY (留空自动生成): " secret_key
if [ -z "$secret_key" ]; then
    secret_key=$(openssl rand -base64 32)
    echo "已生成随机密钥"
fi
railway variables set SECRET_KEY="$secret_key"

# 部署
echo "🚀 部署中..."
railway up

echo "✅ 部署完成！"
echo ""
echo "📝 请记录以下信息："
echo "   - 部署域名: $(railway domain)"
echo "   - SECRET_KEY: $secret_key"
