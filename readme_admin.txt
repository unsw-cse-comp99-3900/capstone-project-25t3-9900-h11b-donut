新增admin端home page，my course page:
已初步完成user story：
1.A1 My course page: creation/deletion for classes 
2.A2 My course page_manage: create tasks with deadlines and upload task detail docs and course learning materials
3.A3 My course page_manage: manage a course question bank

将继续完成A3（student’s Completion% and Overdue, and view a 7-day class on-time trend）和 A4（Risk Report）页面




11.1更新：
1) AdminRiskReport 逻辑修复
	•	Risk tiers 计算规则（严格按公式）：
	•	Red：overdue_parts ≥ 5 或 consecutive_not_on_time_days > 5
	•	Orange：overdue_parts ∈ [2,4] 或 consecutive_not_on_time_days ∈ [2,4]
	•	Yellow：除 Green 外的其他情况（如 1 个 overdue Part 或 1 天 not on time）
	•	Green：从未 overdue 且 consecutive_not_on_time_days = 0
	•	Suggested Action 自动关联：
	•	Red → 1:1 conversation
	•	Orange → warning
	•	Yellow → reminder to prioritize
	•	Green → encouragement
	•	Tips 区域文案优化：
	•	精简 Risk tiers 说明
	•	说明数据口径与“Suggested action 为引导性”性质

2) 新增 Admin 页面：
	•	AdminProfile — 管理员个人信息管理
	•	AdminProgressTrend — 学生进度趋势分析
	•	AdminRiskReport — 学生风险评估报告

三页采用统一布局与视觉，左侧 Sidebar 固定，右侧内容容器滚动，外层卡片边距/阴影/圆角一致。

3) 新增资源
	•	新增 2 个资源文件夹（图标与插图），用于上述页面的 UI 展示。

11.3更新：
	新增 course_admin 的download_material(request, filename)函数 用于下载课程资料