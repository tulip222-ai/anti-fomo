# 一键部署到 Railway (PowerShell 版本)

Write-Host "🚀 开始部署到 Railway..."

# 检查是否安装了 railway CLI
if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "📦 安装 Railway CLI..."
    npm install -g @railway/cli
}

# 登录 Railway (假设已经登录)
# railway login

# 初始化项目 (交互式，如果失败请手动执行 railway init)
# railway init

# 设置环境变量
Write-Host "⚙️ 设置环境变量..."
$secret_key = [Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Minimum 0 -Maximum 255) }))
Write-Host "已生成随机密钥: $secret_key"

# 部署
Write-Host "🚀 部署中..."
railway up

Write-Host "✅ 部署完成！"
Write-Host ""
Write-Host "📝 请记录以下信息："
Write-Host "   - 部署域名: $(railway domain)"
Write-Host "   - SECRET_KEY: $secret_key"
