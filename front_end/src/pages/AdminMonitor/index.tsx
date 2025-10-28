import { useState, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import IconRisk from '../../assets/icons/help-24.svg'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import apiService from '../../services/api'

export function AdminMonitor() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<string>('')
  const [selectedTask, setSelectedTask] = useState<string>('')
  const [selectedView, setSelectedView] = useState<string>('') // 'progress' or 'risk'
  
  type CreatedCourse = {
  id: string;
  title: string;
  description: string;
  illustrationIndex: number;
  tasks: Array<{
    id: string;
    title: string;
    deadline: string;
  }>;
};

const uid = localStorage.getItem('current_user_id') || '';
const safeJSON = <T,>(key: string, fallback: T): T => {
  try {
    const s = localStorage.getItem(key);
    return s ? (JSON.parse(s) as T) : fallback;
  } catch {
    return fallback;
  }
};
const [createdCourses, setCreatedCourses] = useState<CreatedCourse[]>(() => {
  if (!uid) return [];
  // 读取课程数组
  const rawCourses = safeJSON<any[]>(`admin:${uid}:courses`, []);
  // 读取任务映射表
  const tasksMap = safeJSON<Record<string, any[]>>(`admin:${uid}:tasks`, {});
  return rawCourses.map((c) => {
    const courseId = String(c.id ?? c.code); 
    const courseTasks = tasksMap[courseId] ?? [];
    return {
      id: courseId,
      title: c.title ?? '',
      description: c.desc ?? c.description ?? '', // desc → description
      illustrationIndex:
      Number.isFinite(c.illustrationIndex) ? c.illustrationIndex : 0,
      tasks: courseTasks.map((t) => ({
        id:
          t.id != null
            ? String(t.id)
            : `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        title: t.title ?? 'Untitled Task',
        deadline: t.deadline ?? 'No deadline',
      })),
    };
  });
});
  
  const [user, setUser] = useState<{ name?: string; email?: string; avatarUrl?: string } | null>(() => {
    if (!uid) return null;
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'); }
    catch { return null; }
  });

  useEffect(() => {
    // 切换账号后重读 user
    if (uid) {
      try {
        setUser(JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'));
      } catch {
        setUser(null);
      }
    } else {
      setUser(null);
    }
    
    //从这里开始要对接了
    // 监听localStorage变化来更新课程数据
    const handleStorageChange = () => {
      try {
        const saved = localStorage.getItem('admin_created_courses');
        if (saved) {
          setCreatedCourses(JSON.parse(saved));
        }
      } catch {
        setCreatedCourses([]);
      }
    };

    // 添加storage事件监听器
    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [uid]);

  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
    try { await apiService.logout(); }
    finally {
      window.location.hash = '#/login-admin';
      setLogoutModalOpen(false);
    }
  };

  const handleCourseSelect = (courseId: string) => {
    setSelectedCourse(courseId);
    setSelectedTask(''); // 重置task选择
    // 这里可以跳转到具体的监控仪表板页面
    // window.location.hash = `#/admin-monitor-dashboard?courseId=${courseId}`;
  };

  const handleTaskSelect = (taskId: string) => {
    setSelectedTask(taskId);
    setSelectedView(''); // 重置视图选择
    // 这里可以跳转到具体的监控仪表板页面，显示该task的监控数据
    // window.location.hash = `#/admin-monitor-dashboard?courseId=${selectedCourse}&taskId=${taskId}`;
  };

  const handleViewSelect = (viewType: string) => {
    setSelectedView(viewType);
    // 这里可以加载对应的视图内容
  };

  return (
    <div key={uid} className="admin-monitor-layout">
      {/* 左侧导航栏 - 与AdminHome和AdminCourses完全一致 */}
      <aside className="ah-sidebar">
        <div className="ah-profile-card" role="button" aria-label="Open profile" style={{cursor:'pointer'}}>
          <div className="avatar">
            <img
              src={user?.avatarUrl || AvatarIcon}
              width={48}
              height={48}
              alt="avatar"
              style={{ borderRadius: '50%', objectFit: 'cover' }}
              onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
            />
          </div>
          <div className="info">
            <div className="name">{user?.name || 'Admin'}</div>
            <div className="email">{user?.email || 'admin@example.com'}</div>
          </div>
          <button className="chevron" aria-label="Profile" onClick={() => (window.location.hash = '#/admin-profile')}>
            <img src={ArrowRight} width={16} height={16} alt="" />
          </button>
        </div>

        <nav className="ah-nav">
          <a className="item" href="#/admin-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/admin-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item active" href="#/admin-monitor">
            <img src={IconMonitor} className="nav-icon" alt="" /> Analytics
          </a>
        </nav>

        <div className="ah-illustration">
          <img src={adminHomepageImage} alt="Admin Dashboard" style={{ width: '100%', height: 'auto', borderRadius: '20px' }} />
        </div>

        <button className="btn-outline" onClick={handleLogout}>Log Out</button>
      </aside>

      {/* 右侧主内容区域 - 基于Figma设计 */}
      <main className="am-main">
        <header className="am-header">
          <div className="left">
            <div className="hello">Analytics</div>
            <h1 className="title">Select a course and task to view Student Progress (Completion% / Overdue + 7-day trend) or open the Risk Report (Overdue & risk levels).<span className="wave" aria-hidden>😉</span></h1>
          </div>
        </header>

        {/* 课程选择区域 */}
        <section className="am-courses-section">
          {createdCourses.length === 0 ? (
            <div className="courses-empty">
              <div className="title">No Courses found yet.</div>
              <div className="sub">Go to 'My Courses' to create course</div>
            </div>
          ) : (
            <div className="courses-list">
              {createdCourses.map((course) => (
                <div 
                  key={course.id} 
                  className={`course-card ${selectedCourse === course.id ? 'selected' : ''}`}
                  onClick={() => handleCourseSelect(course.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="course-content">
                    <h3 className="course-id">{course.id}</h3>
                    <p className="course-title">{course.title}</p>
                    
                    {/* 始终显示该课程的task按钮 */}
                    {course.tasks && course.tasks.length > 0 ? (
                      <div className="tasks-section">
                        <div className="tasks-label">Select a task:</div>
                        <div className="tasks-list">
                          {course.tasks.map((task) => (
                            <button
                              key={task.id}
                              className={`task-btn ${selectedCourse === course.id && selectedTask === task.id ? 'selected' : ''}`}
                              onClick={(e) => {
                                e.stopPropagation(); // 阻止事件冒泡到课程卡片
                                handleCourseSelect(course.id); // 先选择课程
                                handleTaskSelect(task.id); // 再选择task
                              }}
                            >
                              {task.title}
                              <span className="task-deadline">{task.deadline}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="no-tasks">No tasks available for this course</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 添加新课程按钮 */}
        <div className="add-course-section">
          <button 
            className="add-course-btn"
            onClick={() => window.location.hash = '#/admin-courses'}
          >
            Add new course
          </button>
        </div>

        {/* 视图选择按钮 - 一直显示 */}
        <div className="view-selection-section">
          <div className="view-buttons">
            <button 
              className={`view-btn ${selectedView === 'progress' ? 'selected' : ''}`}
              onClick={() => handleViewSelect('progress')}
            >
              Progress & Trend
            </button>
            <button 
              className={`view-btn ${selectedView === 'risk' ? 'selected' : ''}`}
              onClick={() => handleViewSelect('risk')}
            >
              Risk Report
            </button>
          </div>
        </div>
      </main>

      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={confirmLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Confirm"
        cancelText="Cancel"
      />

      <style>{css}</style>
    </div>
  )
}

/* 管理员监控页面样式 - 与AdminHome和AdminCourses完全一致 */
const css = `
:root{
  --ah-border: #EAEAEA;
  --ah-muted: #6D6D78;
  --ah-text: #172239;
  --ah-card-bg:#FFFFFF;
  --ah-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --ah-primary: #BB87AC; /* 管理员紫色主题 */
  --ah-primary-light: rgba(187, 135, 172, 0.49); /* 半透明紫色 */
}

.admin-monitor-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:48px;
  padding:32px;
  color:var(--ah-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh;
}

.ah-sidebar{
  display:flex;
  flex-direction:column;
  gap:24px;
  height: 100%;
}

/* 侧栏-用户卡 - 与AdminHome完全一致 */
.ah-profile-card{
  display:flex;align-items:center;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:var(--ah-card-bg);box-shadow:var(--ah-shadow);
  height: 95.36px;
}
.ah-profile-card .avatar{
  width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--ah-border);
}
.ah-profile-card .info .name{font-size:16px;font-weight:600}
.ah-profile-card .info .email{color:var(--ah-muted);font-size:12px}
.ah-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--ah-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center}

/* 侧栏-导航 - 与AdminHome完全一致 */
.ah-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
}
.ah-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ah-muted);text-decoration:none;font-weight:500;
}
.ah-nav .item.active{background:var(--ah-primary);color:#172239;font-weight:600;border-radius:20px}
.ah-nav .nav-icon{width:20px;height:20px}

/* 侧栏-插图 - 与AdminHome完全一致 */
.ah-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 侧栏-退出按钮 - 与AdminHome完全一致 */
.btn-outline{
  padding:14px;
  border-radius:14px;
  background:#fff;
  border:1px solid var(--ah-border);
  cursor:pointer;
  font-weight:600;
  margin-top: auto;
}

/* 主内容区域 */
.am-main{
  display:flex;flex-direction:column;
  gap:48px;
}

/* 头部 */
.am-header{
  display:flex;justify-content:space-between;
  align-items:flex-start;
}
.am-header .left{
  display:flex;flex-direction:column;
  gap:8px;
}
.am-header .hello{
  font-size:40px;font-weight:600;
  color:var(--am-text);
}
.am-header .title{
  font-size:16px;font-weight:400;
  color:var(--am-text);
  margin:0;
  line-height:1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 课程区域 */
.am-courses-section{
  flex:1;
}

.courses-list{
  display:flex;flex-direction:column;
  gap:24px;
}

.course-card{
  width: 100%;
  min-height: 108px;
  background: var(--am-card-bg);
  box-shadow: 0px 4px 4px rgba(171.36, 141.86, 141.86, 0.25);
  border-radius: 8px;
  outline: 1px #B876BC solid;
  outline-offset: -1px;
  border-left: 4px solid #BB87AC; /* 左侧紫色竖线，与AdminManageCourse一致 */
  display: flex;
  flex-direction: column;
  padding: 16px 32px;
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
  box-sizing: border-box; /* 确保padding和border包含在元素尺寸内 */
}

.course-card:hover{
  transform: translateY(-2px);
  box-shadow: 0px 8px 16px rgba(171.36, 141.86, 141.86, 0.3);
}

.course-card.selected{
  outline: 2px solid var(--am-primary);
  background: rgba(187, 135, 172, 0.05);
}

.course-content{
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.course-id{
  font-size: 24px;
  font-weight: 600;
  color: var(--am-text);
  margin: 0;
}

.course-title{
  font-size: 16px;
  color: var(--am-muted);
  margin: 0;
}

/* Task按钮样式 */
.tasks-section {
  margin-top: 8px;
  padding-top: 8px;
  width: 100%;
}

.tasks-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--am-text);
  margin-bottom: 6px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
  padding-right: 4px;
}

.tasks-list::-webkit-scrollbar {
  width: 4px;
}

.tasks-list::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 2px;
}

.tasks-list::-webkit-scrollbar-thumb {
  background: var(--am-primary);
  border-radius: 2px;
}

.task-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--am-border);
  border-radius: 6px;
  background: white;
  color: var(--am-text);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 0;
  flex-shrink: 0;
}

.task-btn:hover {
  border-color: var(--am-primary);
  background: rgba(187, 135, 172, 0.05);
}

.task-btn.selected {
  border-color: var(--am-primary);
  background: #8A4B8C; /* 更深的紫色，与背景形成对比 */
  color: white;
  box-shadow: 0 2px 4px rgba(138, 75, 140, 0.3);
  transform: scale(1.02);
}

.task-deadline {
  font-size: 10px;
  color: var(--am-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.task-btn.selected .task-deadline {
  color: rgba(255, 255, 255, 0.8);
}

.no-tasks {
  font-size: 12px;
  color: var(--am-muted);
  font-style: italic;
  margin-top: 8px;
  text-align: center;
  padding: 6px;
  border: 1px dashed var(--am-border);
  border-radius: 6px;
}

/* 空状态 */
.courses-empty{
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  height:300px;text-align:center;
}
.courses-empty .title{
  font-size:24px;font-weight:600;
  color:var(--am-text);
  margin-bottom:8px;
}
.courses-empty .sub{
  font-size:16px;color:var(--am-muted);
}

/* 添加课程按钮区域 */
.add-course-section{
  display:flex;justify-content:flex-end;
  margin-top:32px;
}

.add-course-btn{
  font-size:24px;font-weight:700;
  color:white;
  background:var(--am-primary);
  border:none;border-radius:8px;
  padding:16px 32px;
  cursor:pointer;
  transition:all 0.3s ease;
}

.add-course-btn:hover{
  background:var(--am-primary);
  transform:translateY(-2px);
  box-shadow:0px 8px 16px rgba(187, 135, 172, 0.3);
}

/* 视图选择按钮样式 */
.view-selection-section {
  display: flex;
  justify-content: flex-end; /* 改为右侧对齐 */
  margin-top: 32px;
}

.view-buttons {
  display: flex;
  gap: 24px;
}

.view-btn {
  font-size: 20px;
  font-weight: 600;
  color: white;
  background: #BB87AC; /* 紫色背景 */
  border: 2px solid #BB87AC;
  border-radius: 12px;
  padding: 16px 32px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 200px;
  text-align: center;
}

.view-btn:hover {
  background: #A57598; /* 深紫色悬停 */
  border-color: #A57598;
  transform: translateY(-2px);
  box-shadow: 0px 4px 12px rgba(187, 135, 172, 0.3);
}

.view-btn.selected {
  background: #8A4B8C; /* 更深的紫色选中状态 */
  border-color: #8A4B8C;
  color: white;
  box-shadow: 0px 4px 12px rgba(138, 75, 140, 0.4);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .admin-monitor-layout{
    grid-template-columns: 240px 1fr;
    gap:32px;
    padding:24px;
  }
  
  .course-card{
    width:100%;
    max-width:600px;
  }
  
  .course-id{
    font-size:32px;
  }
}

@media (max-width: 768px) {
  .admin-monitor-layout{
    grid-template-columns:1fr;
    gap:24px;
    padding:16px;
  }
  
  .am-sidebar{
    display:none;
  }
  
  .course-card{
    height:auto;
    padding:24px;
  }
  
  .course-id{
    font-size:24px;
  }
}
`