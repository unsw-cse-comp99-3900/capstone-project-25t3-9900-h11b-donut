# 智能学习计划管理系统
本仓库包含为UNSW COMP9900 capstone项目开发的全栈AI驱动的智能学习计划管理平台。采用单体仓库（monorepo）结构。
---
## 项目背景
在大学学习过程中，学生常常面临课程任务繁多、时间管理困难、缺乏个性化学习指导等问题。为解决这些痛点，我们开发了一个基于人工智能的学习计划管理系统。本项目由 Innovra 客户代表 Jinglin Sun 委托，作为 UNSW COMP9900 Capstone 的业界项目，旨在构建一套基于 Web 的 AI Learning Coach（智能学习教练）原型系统。该系统以大学课程为核心场景，将教学大纲、学习目标与各类评估节点（作业、测验、考试等）自动转化为个性化、可自适应调整的学习路径，帮助学生在整个学期中高效规划学习时间、跟踪学习进度，并提供智能学习辅导。
本系统通过集成Google Gemini AI，实现了智能学习计划生成、个性化学习建议、AI对话辅导、智能题目生成等核心功能，为学生提供全方位的学习管理和辅导支持。同时，管理员端提供课程管理、学生监控、数据分析等功能，帮助教师更好地了解学生学习状况，识别高风险学生并及时干预。
---
## 项目范围
### 智能学习计划生成与调度
系统通过Google Gemini API分析学生的课程任务、截止日期、个人偏好（每日学习时间、每周学习天数、避免学习的日期等），自动生成个性化的周学习计划。AI会根据任务难度、时间紧迫度、任务权重等因素，智能分配每日的学习任务和时长，确保学生能够合理安排时间，高效完成课业。计划生成采用二阶段策略：首先使用Gemini LLM将任务分解为多个学习部分（parts），然后通过智能调度算法将这些部分按学生的个人偏好分配到最优的学习时段。
### AI学习辅导与对话系统
提供智能对话功能，学生可以向AI询问学习计划的原因、任务详情、学习方法等。AI会基于学习计划上下文，提供个性化的解释、鼓励和建议。系统保留7天对话历史，支持上下文连贯的多轮对话。同时，AI可以根据学生自主提供的薄弱知识点自动生成练习题目，并提供即时评分和详细反馈。对话系统采用状态机架构，支持多种对话模式（欢迎、解释计划、练习设置、练习进行等），确保对话流畅自然。
### AI题目生成与智能评分
系统集成了完整的AI题目生成和自动评分模块。管理员可以上传示例题目到数据库，AI基于这些示例生成新的练习题目（支持选择题MCQ和简答题Short Answer）。学生提交答案后，系统自动评分：选择题即时判定，简答题由AI进行语义分析和多维度评分（正确性、完整性、清晰度）。评分结果包含个性化的提示（hint）、完整解答（solution）和详细反馈，帮助学生理解错误并改进。
### 学习进度跟踪与风险识别
系统实时跟踪学生的学习进度和任务完成情况。每个任务支持0-100%的进度更新，学生可以随时查看自己的学习完成度。管理员端可以监控所有学生的学习状况，查看进度趋势图表，并通过算法识别高风险学生（基于逾期任务数量和连续未按时完成天数）。系统会自动生成学生风险报告，并按风险等级由高到低分位红色到绿色，帮助教师及时发现需要帮助的学生并采取干预措施。
### 系统架构
后端采用Django 5.2.7 + Django REST Framework构建RESTful API架构，使用MySQL数据库（生产环境）或SQLite（开发环境）进行数据持久化存储。前端基于React 19 + TypeScript 5.9 + Vite 7构建现代化单页应用，采用Zustand进行轻量级状态管理，使用Recharts进行数据可视化。系统支持Docker容器化部署，通过docker-compose orchestration实现前后端服务的一键启动。采用Nginx作为反向代理服务器，处理静态文件服务和API请求转发。

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

### 核心功能/用户界面
**学生端功能：**
- **Dashboard（学生主页）**：展示课程概览卡片、DDL临近提醒列表、学习进度统计、快速导航入口、未读消息提示
- **Course Management（课程管理）**：浏览可选课程列表、搜索课程、加入/退出课程、查看课程详情页、访问课程学习材料、查看任务列表及截止日期、下载PDF材料
- **Study Plan（学习计划）**：查看AI生成的周学习计划（周视图日历）、每日任务卡片展示、任务完成状态切换、进度条显示、多周计划切换、重新生成计划、调整学习安排
- **AI Chat Coach（AI学习辅导）**：与AI进行多轮对话、获取学习建议和鼓励、解释学习计划原因、生成个性化练习题（MCQ/Short Answer）、即时AI评分反馈、查看对话历史（7天）
- **Profile Management（个人资料）**：管理个人信息、设置学习偏好（每日学习时长、每周学习天数、避免学习日期）、上传头像、保存为默认偏好
- **Message Center（消息中心）**：查看DDL提醒、夜间学习提醒、周奖励消息、系统通知、标记已读/未读、批量操作
**管理员端功能：**
- **Admin Dashboard（管理员仪表板）**：数据统计卡片（课程总数、学生总数、任务总数）、课程管理概览、最近活动展示、快速操作入口
- **Course Management（课程管理）**：创建课程（课程代码、名称、描述、插图选择）、编辑课程信息、删除课程、课程存在性检查
- **Task Management（任务管理）**：创建任务（标题、截止日期、描述、权重百分比、参考链接）、编辑任务、删除任务（可选删除关联文件）、上传任务文件
- **Material Management（材料管理）**：上传学习材料（PDF、文档等）、创建材料条目、编辑材料信息、删除材料、文件管理
- **Question Bank（题库管理）**：上传示例题目（JSON/TXT格式）、批量题目导入、查看题目列表、编辑题目、删除题目、支持MCQ和Short Answer类型
- **Progress Trend（学生监控）**：查看课程学生列表、查看学生任务进度、进度趋势图表展示、筛选特定任务、逾期任务统计
- **Risk Report（风险分析）**：基于算法识别高风险学生、查看学生风险报告（逾期任务数、连续未按时完成天数）、生成风险摘要、导出报告
---
## 项目结构

```
原版capstone-project-25t3-9900-h11b-donut/
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

```
更新版capstone-project-25t3-9900-h11b-donut/
│
├─ front_end/                                         # React + TypeScript frontend application
│  ├─ public/                                         # Static public assets
│  │  ├─ index.html                                   # HTML template
│  │  ├─ vite.svg                                     # Vite logo
│  │  ├─ BATCH_UPLOAD_GUIDE.md                        # Guide for batch question upload
│  │  ├─ PDF_SAMPLE_GUIDE.md                          # PDF upload instructions
│  │  ├─ sample-batch-mcq.json                        # Sample multiple-choice questions in JSON format
│  │  ├─ sample-batch-mcq.txt                         # Sample MCQ in TXT format
│  │  ├─ sample-batch-short.json                      # Sample short answer questions in JSON
│  │  ├─ sample-batch-short.txt                       # Sample short answer in TXT
│  │  ├─ sample-question-mcq.json                     # Single MCQ sample
│  │  ├─ sample-question-mcq.txt                      # Single MCQ in TXT
│  │  ├─ sample-question-short.json                   # Single short answer sample
│  │  ├─ sample-question-short.txt                    # Single short answer in TXT
│  │  └─ test-gemini.html                             # Gemini API test page
│  ├─ src/
│  │  ├─ assets/                                      # Static assets (images, icons, SVGs)
│  │  │  ├─ icons/                                    # UI icon library
│  │  │  │  ├─ arrow-right-16.svg                     # Arrow icon for navigation
│  │  │  │  ├─ bell-24.svg                            # Notification bell icon
│  │  │  │  ├─ chat-24.svg                            # Chat/message icon
│  │  │  │  ├─ courses-24.svg                         # Course management icon
│  │  │  │  ├─ help-24.svg                            # Help/support icon
│  │  │  │  ├─ home-24.svg                            # Home/dashboard icon
│  │  │  │  ├─ plan-24.svg                            # Study plan icon
│  │  │  │  ├─ role-icon-64.svg                       # User role icon
│  │  │  │  ├─ search-24.svg                          # Search icon
│  │  │  │  ├─ settings-24.svg                        # Settings/preferences icon
│  │  │  │  ├─ star-32.svg                            # Star/favorite icon
│  │  │  │  └─ user-24-white.svg                      # User profile icon
│  │  │  ├─ images/                                   # Illustration and image assets
│  │  │  │  ├─ admin-homepage.png                     # Admin dashboard banner
│  │  │  │  ├─ ai-svgrepo-com.png                     # AI assistant icon
│  │  │  │  ├─ illustration-admin.png                 # Admin role illustration
│  │  │  │  ├─ illustration-admin2.png                # Admin interface preview
│  │  │  │  ├─ illustration-admin3.png                # Admin analytics preview
│  │  │  │  ├─ illustration-admin4.png                # Admin management preview
│  │  │  │  ├─ illustration-orange.png                # Orange theme illustration
│  │  │  │  └─ illustration-student.png               # Student role illustration
│  │  │  └─ react.svg                                 # React logo
│  │  ├─ components/                                  # Reusable UI components
│  │  │  ├─ AIChatWidget.tsx                          # AI chat interface widget with collapsible panel
│  │  │  ├─ AvatarPicker.tsx                          # Avatar selection and upload component
│  │  │  ├─ ChatMessage.tsx                           # Individual chat message bubble renderer
│  │  │  ├─ Checkbox.tsx                              # Custom checkbox input component
│  │  │  ├─ ConfirmationModal.tsx                     # Confirmation dialog for critical actions
│  │  │  ├─ DownloadButton.tsx                        # File download button with progress indicator
│  │  │  ├─ DownloadButton.css                        # Styles for download button
│  │  │  ├─ Header.tsx                                # Page header component
│  │  │  ├─ HelpModal.tsx                             # Help documentation modal
│  │  │  ├─ MessageModal.tsx                          # Notification message modal with filtering
│  │  │  ├─ PaginationDots.tsx                        # Pagination indicator dots
│  │  │  ├─ PrimaryButton.tsx                         # Primary action button component
│  │  │  ├─ RoleCard.tsx                              # Role selection card (Student/Admin)
│  │  │  ├─ Sidebar.css                               # Sidebar navigation styles
│  │  │  ├─ TextInput.tsx                             # Text input field component
│  │  │  └─ validators.tsx                            # Form validation utility functions
│  │  ├─ hooks/                                       # Custom React hooks
│  │  │  └─ useUnreadMessagePolling.ts                # Hook for polling unread message count
│  │  ├─ pages/                                       # Page-level route components
│  │  │  ├─ StudentHome/                              # Student dashboard with course overview & DDL reminders
│  │  │  │  └─ index.tsx                              # Main student home page component
│  │  │  ├─ StudentProfile/                           # Profile management with avatar upload & preference settings
│  │  │  │  └─ index.tsx                              # Student profile editing interface
│  │  │  ├─ StudentCourses/                           # Course browsing and enrollment management
│  │  │  │  └─ index.tsx                              # Course search, filter, and enrollment page
│  │  │  ├─ CourseDetail/                             # Course detail page with tasks and materials
│  │  │  │  └─ index.tsx                              # Detailed course view with task list and progress
│  │  │  ├─ StudentPlan/                              # Weekly study plan calendar view
│  │  │  │  └─ index.tsx                              # AI-generated plan display and progress tracking
│  │  │  ├─ ChatWindow/                               # AI chat coaching interface
│  │  │  │  └─ index.tsx                              # Full-screen chat window with conversation history
│  │  │  ├─ PracticeSession/                          # AI-generated practice question session
│  │  │  │  └─ index.tsx                              # Practice mode with AI grading and feedback
│  │  │  ├─ LoginStudent/                             # Student login page
│  │  │  │  └─ index.tsx                              # Student authentication interface
│  │  │  ├─ LoginAdmin/                               # Admin login page
│  │  │  │  └─ index.tsx                              # Admin authentication interface
│  │  │  ├─ SignupStudent/                            # Student registration page
│  │  │  │  └─ index.tsx                              # Student account creation form
│  │  │  ├─ SignupAdmin/                              # Admin registration page
│  │  │  │  └─ index.tsx                              # Admin account creation form
│  │  │  ├─ SignupDesktop/                            # Role selection page (Student/Admin)
│  │  │  │  └─ index.tsx                              # Initial role selection interface
│  │  │  ├─ AdminHome/                                # Admin dashboard with statistics
│  │  │  │  └─ index.tsx                              # Admin overview page with key metrics
│  │  │  ├─ AdminProfile/                             # Admin profile management
│  │  │  │  └─ index.tsx                              # Admin personal information editing
│  │  │  ├─ AdminCourses/                             # Admin course list overview
│  │  │  │  └─ index.tsx                              # List of courses managed by admin
│  │  │  ├─ AdminManageCourse/                        # Detailed course management interface
│  │  │  │  └─ index.tsx                              # Task, material, and question bank management
│  │  │  ├─ AdminMonitor/                             # Student progress monitoring dashboard
│  │  │  │  └─ index.tsx                              # Real-time student progress tracking
│  │  │  ├─ AdminProgressTrend/                       # Student progress trend analysis
│  │  │  │  └─ index.tsx                              # Charts showing student progress over time
│  │  │  └─ AdminRiskReport/                          # At-risk student identification
│  │  │     └─ index.tsx                              # Risk analysis based on overdue tasks and patterns
│  │  ├─ services/                                    # API integration layer
│  │  │  ├─ api.ts                                    # Core API client with authentication and error handling
│  │  │  ├─ aiChatService.ts                          # AI chat conversation API wrapper
│  │  │  ├─ aiPlanService.ts                          # Study plan generation API wrapper
│  │  │  └─ aiQuestionService.ts                      # AI question generation and grading API wrapper
│  │  ├─ store/                                       # State management using Zustand
│  │  │  ├─ coursesStore.ts                           # Student course enrollment and task state
│  │  │  ├─ coursesAdmin.ts                           # Admin course management state
│  │  │  └─ preferencesStore.ts                       # User preferences and study plan state
│  │  ├─ types/                                       # TypeScript type definitions
│  │  │  ├─ assets.d.ts                               # Type declarations for asset imports
│  │  │  ├─ css.d.ts                                  # CSS module type declarations
│  │  │  └─ message.ts                                # Message and notification type definitions
│  │  ├─ utils/                                       # Utility functions
│  │  │  ├─ overdueReport.ts                          # Overdue task report generation
│  │  │  └─ overdueUtils.ts                           # Overdue task calculation utilities
│  │  ├─ App.tsx                                      # Main application component with routing
│  │  ├─ App.css                                      # Global application styles
│  │  ├─ main.tsx                                     # React application entry point
│  │  ├─ index.css                                    # Global CSS reset and base styles
│  │  └─ setupErrorGuards.ts                          # Global error handling setup
│  ├─ .eslintrc.json                                  # ESLint configuration for code quality
│  ├─ .prettierrc                                     # Prettier code formatting rules
│  ├─ .prettierignore                                 # Files to ignore in Prettier
│  ├─ Dockerfile.frontend                             # Docker build configuration for frontend
│  ├─ eslint.config.js                                # ESLint module configuration
│  ├─ index.html                                      # Root HTML template
│  ├─ package.json                                    # NPM dependencies and scripts
│  ├─ package-lock.json                               # Locked dependency versions
│  ├─ tsconfig.json                                   # TypeScript compiler configuration
│  ├─ tsconfig.app.json                               # TypeScript config for application code
│  ├─ tsconfig.node.json                              # TypeScript config for Node.js scripts
│  ├─ vite.config.ts                                  # Vite build tool configuration
│  └─ test.html                                       # Frontend testing HTML page
│
├─ django_backend/                                    # Django REST API backend service
│  ├─ stu_accounts/                                   # Student account management module
│  │  ├─ models.py                                    # Student user model and profile
│  │  ├─ views.py                                     # Student authentication endpoints (login, register, logout)
│  │  ├─ urls.py                                      # Student account URL routing
│  │  ├─ admin.py                                     # Django admin configuration
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for student authentication
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ adm_accounts/                                   # Admin account management module
│  │  ├─ models.py                                    # Admin user model and profile
│  │  ├─ views.py                                     # Admin authentication endpoints (login, register, logout)
│  │  ├─ urls.py                                      # Admin account URL routing
│  │  ├─ admin.py                                     # Django admin configuration
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for admin authentication
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ courses/                                        # Student course enrollment and viewing
│  │  ├─ models.py                                    # Course, Task, Material, and Enrollment models
│  │  ├─ views.py                                     # Course search, enrollment, task retrieval endpoints
│  │  ├─ urls.py                                      # Course-related URL routing
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for course operations
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ courses_admin/                                  # Admin course management module
│  │  ├─ models.py                                    # Admin-owned course and question bank models
│  │  ├─ views.py                                     # Course CRUD, task management, material upload, question bank APIs
│  │  ├─ urls.py                                      # Admin course management URL routing
│  │  ├─ admin.py                                     # Django admin configuration
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for admin operations
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ plans/                                          # Study plan storage and retrieval
│  │  ├─ models.py                                    # WeeklyPlan and PlanItem models
│  │  ├─ views.py                                     # Save/retrieve weekly plans, plan history endpoints
│  │  ├─ services.py                                  # Business logic for plan processing
│  │  ├─ urls.py                                      # Plan-related URL routing
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for plan operations
│  │  ├─ tests_mock.py                                # Mock tests for plan generation
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ preferences/                                    # User study preference management
│  │  ├─ models.py                                    # UserPreference model (daily hours, avoid days, etc.)
│  │  ├─ views.py                                     # Save/retrieve user preferences endpoints
│  │  ├─ urls.py                                      # Preference URL routing
│  │  ├─ admin.py                                     # Django admin configuration
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for preferences
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ task_progress/                                  # Task completion progress tracking
│  │  ├─ models.py                                    # TaskProgress model (student progress percentage)
│  │  ├─ views.py                                     # Update/retrieve task progress endpoints
│  │  ├─ urls.py                                      # Task progress URL routing
│  │  ├─ apps.py                                      # App configuration
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ ai_module/                                      # AI study plan generation core
│  │  ├─ plan_generator.py                            # Main AI plan generation logic using Gemini API
│  │  ├─ scheduler.py                                 # Task scheduling algorithm and time allocation
│  │  ├─ llm_structures.py                            # Structured prompts for Gemini API
│  │  ├─ pdf_ingest.py                                # PDF material parsing and text extraction
│  │  ├─ text_run.py                                  # Text processing utilities
│  │  ├─ types.py                                     # Type definitions for plan generation
│  │  ├─ API_DATA_STRUCTURE.md                        # API data format documentation
│  │  ├─ EXAMPLE_OUTPUT.json                          # Sample AI-generated plan output
│  │  └─ INTEGRATION_GUIDE.md                         # Integration guide for developers
│  ├─ ai_chat/                                        # AI conversation coaching module
│  │  ├─ models.py                                    # ChatMessage, StudyPlan, PracticeSetupState models
│  │  ├─ chat_service.py                              # Main AI chat logic with context management
│  │  ├─ chat_service_simple.py                       # Simplified chat service for testing
│  │  ├─ chat_service_fixed.py                        # Fixed version with bug corrections
│  │  ├─ chat_service.py.bak3                         # Backup version 3
│  │  ├─ chat_service.py.bak4                         # Backup version 4
│  │  ├─ views.py                                     # Chat endpoints: send message, get history, save plan
│  │  ├─ urls.py                                      # AI chat URL routing
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ temp_welcome.py                              # Temporary welcome message generator
│  │  ├─ README.md                                    # AI chat module documentation
│  │  └─ migrations/                                  # Database schema migrations
│  │     ├─ 0005_recentpracticesession.py             # Migration for practice session tracking
│  │     └─ 0006_practicesetupstate_difficulty_and_more.py  # Migration for difficulty settings
│  ├─ ai_question_generator/                          # AI practice question generation module
│  │  ├─ models.py                                    # SampleQuestion, QuestionSession, StudentAnswer models
│  │  ├─ generator.py                                 # AI question generation logic using Gemini API
│  │  ├─ grader.py                                    # AI-powered answer grading and feedback generation
│  │  ├─ views.py                                     # Question generation, answer submission, result retrieval APIs
│  │  ├─ urls.py                                      # AI question generator URL routing
│  │  ├─ admin.py                                     # Django admin for question management
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ management/                                  # Django management commands
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ reminder/                                       # Notification and reminder system
│  │  ├─ models.py                                    # Message model (DDL alerts, nightly notices, bonuses)
│  │  ├─ views.py                                     # Get messages, mark as read endpoints
│  │  ├─ cron.py                                      # Scheduled tasks for automated reminders
│  │  ├─ urls.py                                      # Reminder URL routing
│  │  ├─ admin.py                                     # Django admin for message management
│  │  ├─ apps.py                                      # App configuration
│  │  ├─ tests.py                                     # Unit tests for reminders
│  │  ├─ management/                                  # Django management commands
│  │  └─ migrations/                                  # Database schema migrations
│  ├─ api/                                            # Additional API endpoints
│  │  ├─ study_plan_views.py                          # Study plan generation API endpoint
│  │  └─ urls.py                                      # API URL routing
│  ├─ middleware/                                     # Custom middleware components
│  │  └─ auth_token.py                                # Token authentication and validation middleware
│  ├─ utils/                                          # Shared utility functions
│  │  ├─ auth.py                                      # Authentication helper functions
│  │  └─ validators.py                                # Input validation utilities
│  ├─ project/                                        # Django project configuration
│  │  ├─ settings.py                                  # Django settings (database, apps, middleware, CORS)
│  │  ├─ urls.py                                      # Root URL configuration
│  │  ├─ wsgi.py                                      # WSGI configuration for deployment
│  │  ├─ asgi.py                                      # ASGI configuration for async support
│  │  └─ __init__.py                                  # Package initializer
│  ├─ material/                                       # Course material file storage
│  │  ├─ COMP9321/                                    # Materials for COMP9321 course
│  │  └─ COMP9900/                                    # Materials for COMP9900 course
│  ├─ media/                                          # User-uploaded media files
│  │  ├─ avatars/                                     # User avatar images
│  │  └─ z5540730/                                    # Student-specific uploaded files
│  ├─ task/                                           # Task-related file storage
│  │  ├─ comp1009/                                    # Tasks for COMP1009 course
│  │  ├─ comp9331/                                    # Tasks for COMP9331 course
│  │  ├─ comp9417/                                    # Tasks for COMP9417 course
│  │  └─ comp9900/                                    # Tasks for COMP9900 course
│  ├─ components/                                     # Shared backend components
│  │  └─ 89 - AI Learning Coach_ Goal-Driven Study Planning & Companion.pdf  # Project specification document
│  ├─ manage.py                                       # Django management script
│  ├─ requirements.txt                                # Python package dependencies
│  ├─ Dockerfile.backend                              # Docker build configuration for backend
│  └─ .env                                            # Environment variables (GEMINI_API_KEY, DB config)
│
├─ assets/                                            # Project-wide assets and resources
│  └─ CodeBubbyAssets/                                # Code assistant assets
│
├─ docker-compose.yml                                 # Docker Compose orchestration for backend + frontend
├─ docker-compose.server.yml                          # Production server Docker Compose configuration
├─ .gitignore                                         # Git ignore rules
│
├─ API_DOCUMENTATION.md                               # Complete API endpoint documentation
├─ DEPLOYMENT_GUIDE.md                                # Production deployment instructions
├─ TROUBLESHOOTING_GUIDE.md                           # Common issues and solutions
├─ README.md                                          # Project overview and setup guide
├─ README_new.md                                      # Updated comprehensive README
│
├─ AI_CHAT_SPECIFICATION.md                           # AI chat feature specification
├─ AI_INTEGRATION_UPDATE.md                           # AI integration progress report
├─ AI_QUESTION_INTEGRATION_SUMMARY.md                 # AI question generator integration summary
├─ CONVERSATIONAL_TOPIC_SELECTION_GUIDE.md            # Guide for AI conversation topic handling
├─ CONVERSATIONAL_TOPIC_SELECTION_UPDATE.md           # Updates to conversation topic logic
├─ EXPLAIN_MY_PLAN_FINAL_REPORT.md                   # Plan explanation feature final report
├─ EXPLAIN_MY_PLAN_IMPLEMENTATION_SUMMARY.md          # Implementation summary for plan explanation
├─ PRACTICE_BUTTON_IMPLEMENTATION_SUMMARY.md          # Practice mode implementation summary
├─ PRACTICE_SETUP_MODE_TEST.md                        # Practice setup mode testing documentation
├─ PROJECT_COMPLETION_SUMMARY.md                      # Overall project completion summary
├─ SIMPLIFIED_AI_RESPONSES.md                         # Simplified AI response format guide
├─ UX_IMPROVEMENT_PLAN.md                             # User experience improvement roadmap
├─ UX_IMPROVEMENT_SUMMARY.md                          # UX improvements implementation summary
├─ UX_IMPROVEMENT_COMPLETION_REPORT.md                # UX improvement completion report
├─ FINAL_CONFIRMATION.md                              # Final project confirmation document
├─ FINAL_PROJECT_STATUS_REPORT.md                     # Final status and handover report
├─ TASK_COMPLETION_REPORT.md                          # Task completion tracking report
│
├─ requirements.txt                                   # Python dependencies for testing scripts
├─ pyproject.toml                                     # Python project metadata
│
└─ [Testing & Verification Scripts]/                  # Development and testing utilities
   ├─ test_complete_flow.py                           # End-to-end flow testing
   ├─ test_generate_plan_api.py                       # Plan generation API tests
   ├─ test_practice_generation.py                     # Practice question generation tests
   ├─ test_explain_my_plan.py                         # Plan explanation feature tests
   ├─ test_explain_plan_data.py                       # Plan data validation tests
   ├─ test_ux_improvements.py                         # UX improvement validation tests
   ├─ test_welcome_flow.py                            # Welcome flow testing
   ├─ test_why_plan.py                                # "Why this plan" explanation tests
   ├─ test_ai_plan.py                                 # AI plan generation unit tests
   ├─ test_login_fix.py                               # Login authentication tests
   ├─ test_mysql_connection.py                        # Database connection tests
   ├─ test_plan_content.py                            # Plan content validation
   ├─ test_plan_explanation.py                        # Plan explanation logic tests
   ├─ clean_test.py                                   # Test data cleanup script
   ├─ simple_test.py                                  # Simple functionality tests
   ├─ simple_test2.py                                 # Additional simple tests
   ├─ simple_test_explain.py                          # Simplified explanation tests
   ├─ simple_plan_test.py                             # Simple plan generation tests
   ├─ simple_check.py                                 # Basic system checks
   ├─ quick_verify.py                                 # Quick verification script
   ├─ final_verification.py                           # Final system verification
   ├─ final_comparison.py                             # Final data comparison
   ├─ compare_plan_data.py                            # Plan data comparison utility
   ├─ query_plan_tables.py                            # Database plan table queries
   ├─ verify_plan_json.py                             # Plan JSON validation
   ├─ verify_student_questions.py                     # Student question validation
   ├─ create_test_questions.py                        # Test question generator
   ├─ deep_debug_plan.py                              # Deep debugging for plan generation
   ├─ direct_test.py                                  # Direct API testing
   ├─ complete_explain_test.py                        # Complete explanation feature test
   ├─ valid_token_test.py                             # Token validation tests
   ├─ trace_explain.py                                # Trace explanation logic flow
   ├─ raw_plan_data.json                              # Raw plan data for testing
   ├─ response.json                                   # Sample API response data
   ├─ plan_comparison.txt                             # Plan comparison results
   ├─ final_verification_report.txt                   # Final verification report
   ├─ PLAN_DATA_VERIFICATION_REPORT.txt               # Plan data verification results
   ├─ z1234567_plan_check.txt                         # Student plan check report
   ├─ readme.txt                                      # Testing readme
   ├─ readme_admin.txt                                # Admin testing instructions
   ├─ task_progress_changes.md                        # Task progress feature changes
   ├─ test_button.html                                # Button testing HTML
   ├─ test_button_debug.html                          # Button debug HTML
   ├─ test_frontend_display.html                      # Frontend display testing
   ├─ test_frontend_parsing.html                      # Frontend parsing testing
   └─ todo.json                                       # Development todo list
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



## Setup & Run

### Backend (Local)

```bash
cd django_backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate      # (macOS/Linux)
# or
venv\Scripts\activate          # (Windows)

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create .env file and add:
# GEMINI_API_KEY=your-gemini-api-key
# DB_ENGINE=django.db.backends.sqlite3  # or mysql
# DB_NAME=db.sqlite3
# SECRET_KEY=your-secret-key

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```
🔗 http://localhost:5000

### Frontend (Local)

```bash
cd front_end

# Install dependencies
npm install

# Start development server
npm run dev
```
🔗 http://localhost:5173

### Docker (Backend + Frontend)



## Testing
### Backend
## Backend
Our backend includes comprehensive unit and integration tests to ensure system reliability and correctness.

## Test Coverage
Unit tests verify:
Authentication & Authorization: Student and admin login/register flows, token validation
Course Management: Course CRUD operations, enrollment logic, task retrieval
Study Plan Operations: Plan generation, storage, retrieval, and weekly plan management
AI Integration: Plan generation API calls, chat message handling, question generation workflows
Task Progress Tracking: Progress update logic, completion percentage calculations
Running Backend Tests

### Frontend
