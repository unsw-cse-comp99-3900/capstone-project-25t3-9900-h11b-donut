# 智能学习计划管理系统

## 项目概述

这是一个基于React + TypeScript + Vite构建的智能学习计划管理系统，包含学生端和管理员端两个主要模块。系统提供课程管理、学习计划生成、进度跟踪等功能。

## 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **状态管理**: 自定义Store模式
- **路由**: Hash-based 路由
- **样式**: CSS-in-JS

### 后端
- **框架**: Django
- **数据库**: SQLite (开发环境)
- **API**: RESTful API

## 项目结构

```
capstone-project-25t3-9900-h11b-donut/
├── front_end/                 # 前端项目
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   ├── StudentHome/     # 学生主页
│   │   │   ├── StudentProfile/  # 学生个人资料
│   │   │   ├── StudentCourses/  # 学生课程管理
│   │   │   ├── CourseDetail/    # 课程详情
│   │   │   ├── StudentPlan/     # 学习计划
│   │   │   ├── AdminHome/       # 管理员主页
│   │   │   ├── LoginStudent/    # 学生登录
│   │   │   ├── LoginAdmin/      # 管理员登录
│   │   │   ├── SignupStudent/   # 学生注册
│   │   │   └── SignupAdmin/     # 管理员注册
│   │   ├── components/       # 通用组件
│   │   ├── services/         # API服务
│   │   ├── store/           # 状态管理
│   │   └── assets/          # 静态资源
│   ├── package.json
│   └── vite.config.ts
├── django_backend/           # 后端项目
│   ├── accounts/            # 用户认证
│   ├── courses/            # 课程管理
│   ├── plans/              # 学习计划
│   ├── preferences/        # 用户偏好
│   ├── ai_module/          # AI计划生成模块
│   ├── ai_chat/            # AI对话模块
│   └── utils/              # 工具函数
└── README.md
```

## 功能模块

### 学生端功能
1. **用户认证**
   - 学生注册/登录
   - 路由保护机制
   - Token持久化

2. **个人资料管理**
   - 头像上传和显示
   - 个人信息编辑
   - 偏好设置

3. **课程管理**
   - 查看可选课程
   - 加入/退出课程
   - 课程详情查看

4. **学习计划**
   - AI生成学习计划
   - 周计划视图
   - 进度跟踪

5. **AI对话功能**
   - 智能学习计划解释
   - 任务详情说明
   - 学习鼓励和支持
   - 7天对话历史存储

### 管理员端功能
1. **管理员认证**
   - 管理员注册/登录
   - 独立的路由保护

2. **仪表板**
   - 数据统计展示
   - 课程管理概览
   - 学生状态监控

3. **课程管理**
   - 创建/编辑课程
   - 学生进度查看
   - 任务管理
