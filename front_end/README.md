# AI Web 学习计划应用

本项目是面向初中生的学习计划管理 Web 应用，使用 React + TypeScript + Vite 开发。目标是让学生可以查看课程、任务与周计划，并通过前后端 API 完成登录、偏好设置与资料下载等功能。

当前预览地址（本地开发）：
- http://localhost:5174/

## 项目目标与规则对齐
- 使用 React + TypeScript 构建前端。
- 每个页面为独立目录与函数式组件，组件复用清晰、数据流简单。
- 数据交互统一通过 REST API（后端可为 Express/FastAPI/Django 等），不使用 localStorage 持久化业务数据（仅可用于临时 token 恢复）。
- UI 原型中的交互需要有对应的组件事件逻辑。
- 所有文案对用户展示为英文；代码注释可使用中文。

## 技术栈
- 前端：React 19 + TypeScript
- 构建：Vite 7
- 状态管理：Zustand（后续将过渡为以 API 为主的数据源）
- 样式：内联 CSS / CSS-in-JS
- 路由：Hash 路由
- 服务层：src/services/api.ts（统一封装 fetch 请求）

## 项目结构
```
ai-web/
├── src/
│   ├── assets/                # 图标与图片
│   ├── components/            # 复用组件（Modal、Button、DownloadButton、MessageModal 等）
│   ├── pages/
│   │   ├── StudentHome/
│   │   ├── StudentCourses/
│   │   ├── StudentPlan/
│   │   ├── CourseDetail/
│   │   ├── ChatWindow/        # 新增：AI 教练聊天窗口
│   │   ├── LoginStudent/
│   │   ├── SignupStudent/
│   │   ├── LoginAdmin/
│   │   ├── SignupAdmin/
│   │   ├── StudentProfile/
│   │   ├── AdminHome/
│   │   ├── AdminCourses/
│   │   ├── AdminManageCourse/
│   │   ├── AdminMonitor/
│   │   ├── AdminProgressTrend/
│   │   └── AdminRiskReport/
│   ├── services/
│   │   ├── api.ts             # REST API 封装（认证、课程、任务、偏好、周计划、资料下载）
│   │   └── planGenerator.ts   # 前端计划生成器（将逐步迁移为后端算法/或仅作前端校验）
│   ├── store/                 # 现有本地 store（待逐步替换为 API 数据）
│   └── index.css
├── public/
├── package.json
└── vite.config.ts
```

## 页面说明（英文 UI / 中文注释）
- StudentHome（主页）：课程概览与截止任务列表。当前数据来源仍为本地 store，需改为 API。
- StudentCourses（我的课程）：搜索/添加/移除课程；已将中文注释统一为英文展示，仍依赖本地 store，需改为 API。
- StudentPlan（学习计划）：周计划与偏好设置界面（目前包含前端算法与本地表单），需改为后端 API 生成与保存。
- CourseDetail（课程详情）：任务与学习资料展示。已接入资料列表与下载 API；任务仍来自本地 store，需改为 API。
- ChatWindow（AI 教练聊天窗口）：新增功能，提供个性化学习指导、练习建议和鼓励支持。
- Login/Signup（登录/注册）：表单 UI 完整，缺少真实后端认证调用与表单校验整合。
- StudentProfile（个人资料）：密码与头像等配置 UI，需接入用户配置 API。

## 服务层 API（src/services/api.ts）
- 认证：
  - POST /auth/login  登录（返回 token）
  - POST /auth/logout 登出
- 课程：
  - GET  /courses/available  可选课程列表
  - GET  /courses/my        我的课程
  - POST /courses/add       添加课程
  - DELETE /courses/{id}    移除课程
- 任务：
  - GET  /courses/{id}/tasks        课程任务列表
  - PUT  /tasks/{taskId}/progress   更新任务进度
- 偏好：
  - GET  /preferences
  - PUT  /preferences
- 周计划：
  - GET  /plans/weekly/{weekOffset}
  - PUT  /plans/weekly/{weekOffset}
- 学习材料：
  - GET  /courses/{id}/materials    材料列表
  - GET  /materials/{materialId}/download  下载

说明：
- apiService 内置 token 持久化初始化（localStorage 仅用于恢复 token）。
- 业务数据（课程、任务、计划、偏好）必须来源于后端 API，而非本地 store。

## 当前未完成功能清单（需要前端改造与 API 接入）
1. 数据源统一化
   - StudentHome/StudentCourses/StudentPlan/StudentProfile 等页面仍使用 coursesStore 的本地数据与逻辑。
   - 需要将这些页面的读取与更新逻辑替换为 apiService 调用，并用组件内部状态管理接入结果。
2. 认证与鉴权
   - Login/Signup 页面需要接入 /auth/login 与 /auth/signup（若后端提供），并在登录后保存 token、跳转首页。
   - 登出逻辑统一调用 /auth/logout，并清理 token。
3. 课程管理
   - “我的课程”列表、搜索与添加/移除需改为 API 数据。
   - 点击课程卡片进入详情时，应先通过 API 拉取课程详情与任务。
4. 任务进度
   - 任务完成/进度更新调用 PUT /tasks/{taskId}/progress，并在前端刷新展示。
5. 偏好设置与周计划
   - 偏好设置保存与读取调用 /preferences。
   - 周计划读取与保存调用 /plans/weekly/{weekOffset}。
   - 前端的 planGenerator.ts 可保留为校验或兜底逻辑，但主生成流程应走后端。
6. 资料模块
   - 课程详情页学习材料已接入 API；仍需在无材料时展示空态与错误处理统一。
7. 表单与校验
   - 登录/注册/资料编辑需要统一的校验与错误提示；占位的头像上传需补齐上传组件与后端接口。
8. UI 一致性与可访问性
   - 检查按钮 aria-label、焦点状态、滚动区域等，确保所有交互均可键盘访问。
9. 英文文案/中文注释规范
   - 展示文案保持英文，中文仅用于代码注释；已发现的中文展示文案已基本清理，但仍需在所有页面复核。

## 建议的改造顺序（前端实现计划）
- 阶段 1：认证打通
  - 接入 login/logout，登录后将 token 设置到 apiService，并跳转 student-home。
- 阶段 2：课程页数据统一
  - StudentCourses：用 getAvailableCourses / getUserCourses 替换本地数据；添加/移除课程调用后端。
  - StudentHome：课程概览与 Deadlines 改为使用后端任务/进度数据。
- 阶段 3：课程详情与任务进度
  - CourseDetail：任务改为 getCourseTasks；进度更新走 updateTaskProgress；维持已接入的资料列表与下载。
- 阶段 4：偏好设置与周计划
  - StudentPlan：读取/保存偏好与周计划走 API；planGenerator 仅作可行性检查与提示。
- 阶段 5：个人资料与注册
  - StudentProfile/Signup：补充头像上传组件与后端接口，完善表单校验与错误处理。
- 阶段 6：一致性与优化
  - 统一空态、加载态、错误态；抽离 Loading/Empty/Error 组件；加强无障碍支持。

## 开发与运行
### 环境要求
- Node.js 18+
- npm

### 安装与启动
```bash
cd ai-web
npm install
npm run dev   # 默认尝试 5173，若占用将自动切换端口（如 5174）
```
浏览器访问：
- http://localhost:5174/ （或终端提示的端口）

### 构建与预览
```bash
npm run build
npm run preview
```

### 代码检查
```bash
npm run lint
```

## 说明与后续优化
- 目前页面已基本完成布局与交互框架，数据源正从本地 store 迁移到统一的 REST API。
- 当后端 API 未就绪时，可在 api.ts 内使用临时 mock（仅开发阶段），一旦后端可用应切换到真实接口。
- 逐步将中文展示文案转为英文，中文仅用于代码注释，已在 StudentCourses/CourseDetail 等页处理。
- 浏览器兼容：现代浏览器（Chrome/Firefox/Safari/Edge）。


## 完成度状态（持续更新）
- [x] 基本页面与组件结构
- [x] 课程详情页接入材料列表与下载 API
- [x] Plan 进度与截止日期进度条优化
- [x] 消息弹窗系统集成
- [x] AI Chat Window 功能实现
- [ ] 登录/登出接入后端
- [ ] 我的课程（列表/搜索/添加/移除）接入后端
- [ ] 任务列表与进度更新接入后端
- [ ] 偏好设置与周计划接入后端
- [ ] 个人资料与头像上传接入后端
- [ ] 表单校验与错误提示统一
- [ ] Loading/Empty/Error 组件抽象与无障碍优化


11.2
## 11.2 Student_end更新修复内容
### 1. Plan 进度与截止日期进度条
- 修复了 StudentPlan 页面中任务进度条的显示问题
- 优化了进度条与截止日期的视觉关联性
- 确保进度条准确反映任务完成状态

#### 前端实现细节与重要参数
**相关文件**: `front_end/src/pages/StudentPlan/index.tsx`

**进度条数据结构**:
```typescript
interface TaskProgress {
  taskId: string
  taskName: string
  progress: number // 0-100 的进度百分比
  deadline: string  // ISO 日期字符串
  status: 'pending' | 'in-progress' | 'completed' | 'overdue'
  parts: Array<{
    partId: string
    partName: string
    completed: boolean
    required: boolean
  }>
}
```

**进度计算逻辑**:
```typescript
// 计算任务整体进度
const calculateTaskProgress = (task: Task) => {
  const totalParts = task.parts.length
  const completedParts = task.parts.filter(part => part.completed).length
  return Math.round((completedParts / totalParts) * 100)
}

// 判断任务状态
const getTaskStatus = (task: Task) => {
  const now = new Date()
  const deadline = new Date(task.deadline)
  
  if (task.progress === 100) return 'completed'
  if (now > deadline) return 'overdue'
  if (task.progress > 0) return 'in-progress'
  return 'pending'
}
```

**进度条组件关键参数**:
```typescript
// 进度条颜色映射
const progressColors = {
  completed: '#10B981', // 绿色 - 已完成
  'in-progress': '#3B82F6', // 蓝色 - 进行中
  overdue: '#EF4444', // 红色 - 已逾期
  pending: '#6B7280' // 灰色 - 未开始
}

// 进度条样式配置
const progressBarConfig = {
  height: '8px',
  borderRadius: '4px',
  transition: 'width 0.3s ease',
  minWidth: '8px' // 确保即使进度为0也有最小宽度
}
```

**后端接口建议**:
```typescript
// 获取学生计划进度
GET /api/students/{studentId}/plan-progress
Response: {
  weeklyPlan: {
    weekStart: string
    weekEnd: string
    tasks: Array<TaskProgress>
  }
  overallProgress: number // 整体进度百分比
  overdueTasks: number    // 逾期任务数量
  completedThisWeek: number // 本周完成的任务数量
}

// 更新任务进度
PUT /api/tasks/{taskId}/progress
Request: {
  progress: number
  completedParts?: Array<string> // 完成的part ID列表
}

// 标记part完成状态
PUT /api/tasks/{taskId}/parts/{partId}
Request: {
  completed: boolean
}
```

**前端-后端数据同步要点**:
1. **实时进度更新**: 当用户标记part完成时，立即调用API更新进度
2. **状态一致性**: 前端根据deadline和progress计算状态，后端需要确保数据准确
3. **缓存策略**: 考虑使用乐观更新，先更新UI再同步到后端
4. **错误处理**: 进度更新失败时提供回滚机制

### 2. 新增消息弹窗系统
- 新增 `MessageModal` 组件，提供统一的消息通知界面
- 支持多种消息类型：due alerts、nightly notices、admin DDL 变更等
- 优化消息显示延迟问题，提升用户体验
- 集成到所有相关页面，提供一致的消息交互体验

### 3. 新增 AI Chat Window
- 新增 `ChatWindow` 页面，提供个性化 AI 学习教练功能
- 支持多种交互模式：
  - **Explain my plan** - 详细解释学习计划
  - **Practice my weak topics** - 针对薄弱主题的练习建议
  - **How to do for Part N of Task X** - 具体任务指导
  - **Give me some encouragement** - 学习鼓励与支持
- 集成到 StudentHome、StudentCourses、CourseDetail、StudentPlan 页面
- 提供智能对话响应，根据用户输入生成针对性建议

## 消息盒子与 AI Chat 后端接入说明

### 消息盒子系统后端接入
当前消息系统使用前端模拟数据，接入后端需要：

#### 1. 消息 API 接口设计
```typescript
// 获取用户消息列表
GET /api/messages
Response: {
  messages: Array<{
    id: string
    type: 'due_alert' | 'nightly_notice' | 'admin_ddl_change' | 'system'
    title: string
    content: string
    timestamp: string
    read: boolean
  }>
}

// 标记消息为已读
PUT /api/messages/{messageId}/read

// 获取未读消息数量
GET /api/messages/unread-count
```

#### 2. 前端接入步骤
- 在 `api.ts` 中添加消息相关 API 方法
- 修改 `MessageModal` 组件，将模拟数据替换为 API 调用
- 在相关页面添加消息轮询机制，实时更新未读消息
- 添加消息已读状态同步逻辑

### AI Chat Window 后端接入
当前 AI Chat 使用前端模拟对话，接入后端需要：

#### 1. AI 对话 API 接口设计
```typescript
// 发送消息给 AI 教练
POST /api/ai/chat
Request: {
  message: string
  context?: {
    currentCourse?: string
    currentTask?: string
    userPreferences?: any
  }
}
Response: {
  response: string | React.ReactNode
  suggestions?: Array<string> // 后续建议
  practiceSession?: {
    questions: Array<any>
    duration: number
  }
}

// 获取对话历史
GET /api/ai/chat/history

// 开始练习会话
POST /api/ai/practice/start
```

#### 2. 前端接入步骤
- 在 `api.ts` 中添加 AI 对话相关 API 方法
- 修改 `ChatWindow` 组件的 `onSend` 函数，调用真实 AI 接口
- 将模拟的练习题目替换为后端生成的个性化练习
- 添加对话历史保存和恢复功能
- 集成用户学习数据，提供更精准的个性化建议

#### 3. 个性化功能增强
- **学习数据分析**：基于用户学习进度和成绩数据生成针对性建议
- **智能练习生成**：根据用户薄弱知识点动态生成练习题
- **进度跟踪**：记录用户与 AI 教练的互动，优化建议算法
- **多模态支持**：支持文本、图片、代码等多种交互形式

### 接入优先级建议
1. **第一阶段**：消息系统基础接入（获取消息、标记已读）
2. **第二阶段**：AI Chat 基础对话功能接入
3. **第三阶段**：个性化练习和智能建议功能
4. **第四阶段**：高级功能（学习数据分析、多模态交互）