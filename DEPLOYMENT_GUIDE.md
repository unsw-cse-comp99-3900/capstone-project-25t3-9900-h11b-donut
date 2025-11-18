# 智能学习计划管理系统 - 部署指南

## 🚀 部署概述

本指南将帮助您将智能学习计划管理系统部署到生产环境。系统采用前后端分离架构，支持多种部署方式。

## 📋 部署前准备

### 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+) / macOS / Windows
- **Python**: 3.9+
- **Node.js**: 16+
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **Web服务器**: Nginx (推荐) / Apache
- **反向代理**: Nginx
- **SSL证书**: Let's Encrypt (推荐)

### 环境变量配置
创建 `.env` 文件：
```bash
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库配置
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# AI配置
GEMINI_API_KEY=your-gemini-api-key

# 安全配置
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 🐳 Docker部署 (推荐)

### 1. 创建Docker Compose文件
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: learning_system
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./django_backend
    command: gunicorn --bind 0.0.0.0:8001 django_backend.wsgi:application
    volumes:
      - ./django_backend:/app
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8001:8001"
    depends_on:
      - db
    environment:
      - DEBUG=False
      - DB_HOST=db
      - DB_NAME=learning_system
      - DB_USER=postgres
      - DB_PASSWORD=password

  frontend:
    build: ./front_end
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### 2. 创建Dockerfile

#### 后端Dockerfile
```dockerfile
# django_backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "django_backend.wsgi:application"]
```

#### 前端Dockerfile
```dockerfile
# front_end/Dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🖥️ 传统部署方式

### 1. 后端部署

#### 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### 数据库配置
```bash
# 创建PostgreSQL数据库
sudo -u postgres createdb learning_system
sudo -u postgres createuser --interactive

# 运行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic --noinput
```

#### 启动Gunicorn
```bash
# 创建gunicorn配置文件
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8001"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = False
user = "www-data"
group = "www-data"
tmp_upload_dir = None
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
EOF

# 启动gunicorn
gunicorn --config gunicorn.conf.py django_backend.wsgi:application
```

#### 创建systemd服务
```bash
# 创建服务文件
sudo cat > /etc/systemd/system/learning-system-backend.service << EOF
[Unit]
Description=Learning System Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/django_backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --config gunicorn.conf.py django_backend.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl enable learning-system-backend
sudo systemctl start learning-system-backend
sudo systemctl status learning-system-backend
```

### 2. 前端部署

#### 构建生产版本
```bash
cd front_end
npm ci --only=production
npm run build
```

#### 配置Nginx
```nginx
# /etc/nginx/sites-available/learning-system
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL配置
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 前端静态文件
    location / {
        root /path/to/front_end/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        alias /path/to/django_backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/django_backend/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

#### 启用站点
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/learning-system /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

## 🔒 SSL证书配置

### Let's Encrypt (推荐)
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控和日志

### 1. 应用监控
```bash
# 安装监控工具
pip install django-debug-toolbar  # 开发环境
pip install sentry-sdk  # 生产环境错误追踪
```

### 2. 日志配置
```python
# django_backend/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/learning-system.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## 🔄 备份策略

### 数据库备份
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -h localhost -U postgres learning_system > $BACKUP_DIR/db_backup_$DATE.sql

# 媒体文件备份
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /path/to/django_backend/media/

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 自动备份
```bash
# 添加到crontab
0 2 * * * /path/to/backup.sh
```

## 🚀 性能优化

### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_courses_active ON courses_course(is_active);
CREATE INDEX CONCURRENTLY idx_student_enrollment ON courses_studentenrollment(student_id, course_code);

-- 分析表统计信息
ANALYZE;
```

### 2. 缓存配置
```python
# django_backend/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 🔧 故障排除

### 常见问题

#### 1. 静态文件404
```bash
# 检查Nginx配置
sudo nginx -t

# 检查文件权限
sudo chown -R www-data:www-data /path/to/static/
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U postgres -d learning_system
```

#### 3. API请求超时
```bash
# 检查Gunicorn状态
sudo systemctl status learning-system-backend

# 查看错误日志
sudo tail -f /var/log/gunicorn/error.log
```

## 📈 扩展部署

### 负载均衡
```nginx
upstream backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### 水平扩展
```bash
# 启动多个Gunicorn worker
gunicorn --workers 4 --bind 127.0.0.1:8001 django_backend.wsgi:application
gunicorn --workers 4 --bind 127.0.0.1:8002 django_backend.wsgi:application
gunicorn --workers 4 --bind 127.0.0.1:8003 django_backend.wsgi:application
```

---

## 🎯 部署检查清单

### 部署前
- [ ] 环境变量配置完成
- [ ] 数据库创建和迁移
- [ ] SSL证书获取
- [ ] 防火墙配置
- [ ] 备份策略制定

### 部署中
- [ ] 代码部署到服务器
- [ ] 依赖安装
- [ ] 静态文件收集
- [ ] 服务启动
- [ ] Nginx配置

### 部署后
- [ ] 功能测试
- [ ] 性能测试
- [ ] 安全检查
- [ ] 监控配置
- [ ] 日志配置

---

**部署完成后，您的智能学习计划管理系统将可以在生产环境中稳定运行！** 🎉