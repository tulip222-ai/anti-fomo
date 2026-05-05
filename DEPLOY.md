# 反 FOMO 部署指南

## 方案一：Railway（推荐，免费）

Railway 提供免费额度，支持一键部署，适合快速上线。

### 步骤

1. **Fork 或上传代码到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **在 Railway 创建项目**
   - 访问 https://railway.app
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择你的仓库

3. **配置环境变量**
   - 在项目设置中添加：
     - `SECRET_KEY`: 随机字符串（用于 JWT 签名）

4. **部署完成**
   - Railway 会自动构建并部署
   - 获得域名如 `https://anti-fomo.up.railway.app`

---

## 方案二：Render（免费）

Render 也提供免费托管服务。

### 步骤

1. **推送代码到 GitHub**

2. **在 Render 创建 Web Service**
   - 访问 https://render.com
   - 点击 "New" → "Web Service"
   - 连接 GitHub 仓库

3. **配置**
   - 名称: `anti-fomo`
   - 运行时: `Python 3`
   - 构建命令: `pip install -r requirements.txt`
   - 启动命令: `gunicorn -w 4 -b 0.0.0.0:10000 app:app`

4. **添加环境变量**
   - `SECRET_KEY`: 随机字符串

---

## 方案三：Vercel（仅前端）

Vercel 适合纯前端部署，后端功能需另行部署。

### 步骤

1. **安装 Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **部署**
   ```bash
   cd anti-fomo-backend
   vercel
   ```

3. **注意**: Vercel 的免费版不支持 SQLite 持久化存储，需要：
   - 使用外部数据库（如 Supabase、PlanetScale）
   - 或改用 Railway/Render 部署完整后端

---

## 方案四：Docker 部署（自己的服务器）

适合有云服务器的用户（阿里云、腾讯云、AWS 等）。

### 步骤

1. **安装 Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

2. **克隆代码**
   ```bash
   git clone <your-repo>
   cd anti-fomo-backend
   ```

3. **启动服务**
   ```bash
   # 设置密钥
   export SECRET_KEY="your-random-secret-key"
   
   # 启动
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f
   ```

5. **更新部署**
   ```bash
   docker-compose down
   git pull
   docker-compose up -d --build
   ```

---

## 方案五：云服务器手动部署

### 环境要求
- Python 3.8+
- pip3

### 步骤

1. **上传代码到服务器**
   ```bash
   scp -r anti-fomo-backend root@your-server-ip:/opt/
   ```

2. **安装依赖**
   ```bash
   cd /opt/anti-fomo-backend
   pip3 install -r requirements.txt
   ```

3. **使用 Gunicorn 启动**
   ```bash
   export SECRET_KEY="your-random-secret-key"
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **配置 Nginx 反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **使用 systemd 守护进程**
   ```bash
   sudo nano /etc/systemd/system/anti-fomo.service
   ```
   
   内容：
   ```ini
   [Unit]
   Description=Anti FOMO Service
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/opt/anti-fomo-backend
   Environment="SECRET_KEY=your-secret-key"
   ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   启动：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable anti-fomo
   sudo systemctl start anti-fomo
   ```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `SECRET_KEY` | JWT 签名密钥 | ✅ |
| `FLASK_ENV` | 运行环境 (production/development) | ❌ |

### 生成随机密钥

```bash
openssl rand -base64 32
```

---

## 域名配置

部署完成后，建议配置自定义域名：

1. 在域名服务商添加 A 记录指向服务器 IP
2. 配置 HTTPS（使用 Let's Encrypt）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com
```

---

## 监控与维护

### 查看日志
```bash
# Docker
docker-compose logs -f

# systemd
sudo journalctl -u anti-fomo -f
```

### 备份数据
```bash
# 备份 SQLite 数据库
cp anti_fomo.db anti_fomo.db.backup.$(date +%Y%m%d)
```

---

## 各方案对比

| 方案 | 难度 | 费用 | 适用场景 |
|------|------|------|----------|
| Railway | ⭐ 简单 | 免费额度 | 快速上线、个人项目 |
| Render | ⭐ 简单 | 免费额度 | 快速上线、个人项目 |
| Vercel | ⭐ 简单 | 免费 | 仅前端展示 |
| Docker | ⭐⭐ 中等 | 服务器费用 | 生产环境、团队协作 |
| 云服务器 | ⭐⭐⭐ 较难 | 服务器费用 | 大规模生产环境 |

---

## 推荐组合

**个人/小项目**: Railway/Render（免费，一键部署）

**生产环境**: 阿里云/腾讯云 + Docker + Nginx（稳定可控）
