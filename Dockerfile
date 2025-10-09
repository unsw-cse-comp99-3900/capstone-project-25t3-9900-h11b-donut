#参考docker_primer
# 与本地一致的 Python 版本
FROM python:3.11.5-slim

# 避免生成 .pyc，输出不缓存
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装 bcrypt 等依赖可能需要的编译工具 / 或删除这一段
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 拷贝依赖文件并安装
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝项目代码
COPY . .

# 声明端口
EXPOSE 9900

# 启动应用
CMD ["python", "app.py"]
