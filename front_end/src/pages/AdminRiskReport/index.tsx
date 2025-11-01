import { useState, useEffect, useMemo } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import apiService from '../../services/api'

type StudentRisk = {
  id: string;
  name: string;
  studentId: string;
  riskTier: 'Red' | 'Orange' | 'Yellow' | 'Green';
  overdueParts: number;
  suggestedAction: string;
  consecutiveNotOnTimeDays: number;
};

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

export function AdminRiskReport() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<string>('')
  const [selectedTask, setSelectedTask] = useState<string>('')
  const [students, setStudents] = useState<StudentRisk[]>([])
  const [filteredStudents, setFilteredStudents] = useState<StudentRisk[]>([])
  const [riskFilter, setRiskFilter] = useState<string[]>(['Red', 'Orange', 'Yellow', 'Green'])
  const [searchTerm, setSearchTerm] = useState<string>('')
  
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
    const rawCourses = safeJSON<any[]>(`admin:${uid}:courses`, []);
    const tasksMap = safeJSON<Record<string, any[]>>(`admin:${uid}:tasks`, {});
    return rawCourses.map((c) => {
      const courseId = String(c.id ?? c.code); 
      const courseTasks = tasksMap[courseId] ?? [];
      return {
        id: courseId,
        title: c.title ?? '',
        description: c.desc ?? c.description ?? '',
        illustrationIndex: Number.isFinite(c.illustrationIndex) ? c.illustrationIndex : 0,
        tasks: courseTasks.map((t) => ({
          id: t.id != null ? String(t.id) : `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
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
    const getParams = () => {
      if (window.location.hash.includes('?')) {
        return new URLSearchParams(window.location.hash.split('?')[1]);
      }
      return new URLSearchParams(window.location.search.replace(/^\?/, ''));
    };
    
    const params = getParams();
    const courseId = params.get('courseId');
    const taskId = params.get('taskId');
    
    if (courseId && taskId) {
      setSelectedCourse(courseId);
      setSelectedTask(taskId);
      loadStudentRiskData(courseId, taskId);
    }
  }, []);

  // 计算Risk tier的函数
  const calculateRiskTier = (overdueParts: number, consecutiveNotOnTimeDays: number): 'Red' | 'Orange' | 'Yellow' | 'Green' => {
    // Red — overdue_parts ≥ 5 OR consecutive_not_on_time_days > 5
    if (overdueParts >= 5 || consecutiveNotOnTimeDays > 5) {
      return 'Red';
    }
    
    // Orange — overdue_parts ∈ [2,4] OR consecutive_not_on_time_days ∈ [2,4]
    if ((overdueParts >= 2 && overdueParts <= 4) || (consecutiveNotOnTimeDays >= 2 && consecutiveNotOnTimeDays <= 4)) {
      return 'Orange';
    }
    
    // Green — never overdue and 0 consecutive not-on-time days
    if (overdueParts === 0 && consecutiveNotOnTimeDays === 0) {
      return 'Green';
    }
    
    // Yellow — other non-Green cases (e.g., one overdue Part or 1 day not on time)
    return 'Yellow';
  };

  // 根据Risk tier获取Suggested Action
  const getSuggestedAction = (riskTier: 'Red' | 'Orange' | 'Yellow' | 'Green'): string => {
    switch (riskTier) {
      case 'Red': return '1:1 conversation';
      case 'Orange': return 'warning';
      case 'Yellow': return 'reminder to prioritize';
      case 'Green': return 'encouragement';
      default: return 'encouragement';
    }
  };

  const loadStudentRiskData = (courseId: string, taskId: string) => {
    console.log('Loading student risk data for course:', courseId, 'task:', taskId);
    
    // ============================================
    // 🚨 MOCK DATA SECTION - 学生风险数据 🚨
    // ============================================
    // TODO: 这里需要替换为真实的后端API调用
    // 生成mock学生风险数据，用于测试各种风险等级情况
    // ============================================
    
    // Mock数据 - 包含各种测试情况
    const mockStudentData = [
      // Red cases
      { id: '1', name: 'Alice Johnson', studentId: 'z1234567', overdueParts: 5, consecutiveNotOnTimeDays: 6 },
      { id: '6', name: 'Frank Miller', studentId: 'z6789012', overdueParts: 7, consecutiveNotOnTimeDays: 8 },
      { id: '10', name: 'Jack Taylor', studentId: 'z0123456', overdueParts: 6, consecutiveNotOnTimeDays: 7 },
      { id: '16', name: 'Paul Anderson', studentId: 'z6677889', overdueParts: 8, consecutiveNotOnTimeDays: 9 },
      { id: '20', name: 'Tina Moore', studentId: 'z0011223', overdueParts: 5, consecutiveNotOnTimeDays: 6 },
      
      // Orange cases
      { id: '2', name: 'Bob Smith', studentId: 'z2345678', overdueParts: 3, consecutiveNotOnTimeDays: 3 },
      { id: '5', name: 'Eva Brown', studentId: 'z5678901', overdueParts: 2, consecutiveNotOnTimeDays: 2 },
      { id: '9', name: 'Ivy Wang', studentId: 'z9012345', overdueParts: 4, consecutiveNotOnTimeDays: 4 },
      { id: '13', name: 'Mia Rodriguez', studentId: 'z3344556', overdueParts: 3, consecutiveNotOnTimeDays: 2 },
      { id: '17', name: 'Quinn Harris', studentId: 'z7788990', overdueParts: 2, consecutiveNotOnTimeDays: 3 },
      
      // Yellow cases
      { id: '3', name: 'Carol Davis', studentId: 'z3456789', overdueParts: 1, consecutiveNotOnTimeDays: 1 },
      { id: '7', name: 'Grace Lee', studentId: 'z7890123', overdueParts: 1, consecutiveNotOnTimeDays: 0 },
      { id: '11', name: 'Karen White', studentId: 'z1122334', overdueParts: 1, consecutiveNotOnTimeDays: 1 },
      { id: '14', name: 'Nathan Kim', studentId: 'z4455667', overdueParts: 1, consecutiveNotOnTimeDays: 0 },
      { id: '18', name: 'Rachel Scott', studentId: 'z8899001', overdueParts: 1, consecutiveNotOnTimeDays: 1 },
      
      // Green cases
      { id: '4', name: 'David Wilson', studentId: 'z4567890', overdueParts: 0, consecutiveNotOnTimeDays: 0 },
      { id: '8', name: 'Henry Chen', studentId: 'z8901234', overdueParts: 0, consecutiveNotOnTimeDays: 0 },
      { id: '12', name: 'Leo Garcia', studentId: 'z2233445', overdueParts: 0, consecutiveNotOnTimeDays: 0 },
      { id: '15', name: 'Olivia Martin', studentId: 'z5566778', overdueParts: 0, consecutiveNotOnTimeDays: 0 },
      { id: '19', name: 'Samuel Young', studentId: 'z9900112', overdueParts: 0, consecutiveNotOnTimeDays: 0 },
    ];
    
    // 动态计算Risk tier和Suggested Action
    const mockStudents: StudentRisk[] = mockStudentData.map(student => {
      const riskTier = calculateRiskTier(student.overdueParts, student.consecutiveNotOnTimeDays);
      const suggestedAction = getSuggestedAction(riskTier);
      
      return {
        ...student,
        riskTier,
        suggestedAction
      };
    });
    
    setStudents(mockStudents);
    setFilteredStudents(mockStudents);
  };

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

  const getSelectedCourse = () => {
    return createdCourses.find(course => course.id === selectedCourse);
  };

  const getSelectedTask = () => {
    const course = getSelectedCourse();
    return course?.tasks.find(task => task.id === selectedTask);
  };

  // 风险过滤器切换
  const toggleRiskFilter = (tier: string) => {
    setRiskFilter(prev => 
      prev.includes(tier) 
        ? prev.filter(t => t !== tier)
        : [...prev, tier]
    );
  };

  // 获取风险等级颜色
  const getRiskColor = (tier: string) => {
    switch (tier) {
      case 'Red': return '#FF6B6B';
      case 'Orange': return '#FFA500';
      case 'Yellow': return '#FFD700';
      case 'Green': return '#4CAF50';
      default: return '#6D6D78';
    }
  };

  // 过滤和搜索逻辑
  useEffect(() => {
    let result = [...students];
    
    // 应用风险过滤器
    if (riskFilter.length > 0 && riskFilter.length < 4) {
      result = result.filter(student => riskFilter.includes(student.riskTier));
    }
    
    // 应用搜索过滤器
    if (searchTerm) {
      result = result.filter(student => 
        student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.studentId.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // 按照指定优先级进行排序
    result.sort((a, b) => {
      // 第一键：Risk 严重度（Red → Orange → Yellow → Green）
      const riskOrder = { 'Red': 0, 'Orange': 1, 'Yellow': 2, 'Green': 3 };
      const riskDiff = riskOrder[a.riskTier] - riskOrder[b.riskTier];
      if (riskDiff !== 0) return riskDiff;
      
      // 第二键：Overdue Parts 降序（数字大的在前）
      const overdueDiff = b.overdueParts - a.overdueParts;
      if (overdueDiff !== 0) return overdueDiff;
      
      // 第三键：Student Name A→Z（字母序稳定）
      return a.name.localeCompare(b.name);
    });
    
    setFilteredStudents(result);
  }, [students, riskFilter, searchTerm]);

  return (
    <div key={uid} className="admin-progress-trend-layout">
      {/* 左侧导航栏 - 与AdminProgressTrend完全一致 */}
      <aside className="ah-sidebar">
        <div className="ah-profile-card">
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
          <button className="chevron" aria-label="Open profile" onClick={() => (window.location.hash = '#/admin-profile')}>
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

      {/* 右侧主内容区域 - 最外侧包裹框 */}
      <div className="apt-outer-container">
        <main className="apt-main">
          <header className="apt-header">
            <div className="header-content">
              <div className="cd-hero-clean">
                <button
                  className="back-circle"
                  aria-label="Back to Analytics"
                  onClick={() => window.location.hash = '#/admin-monitor'}
                >
                  <img src={ArrowRight} width={16} height={16} alt="" className="chev-left" />
                </button>
              </div>
              <div className="left">
                <div className="hello">Risk Report</div>
                <h1 className="title">
                  {getSelectedCourse()?.title || 'Course'} - {getSelectedTask()?.title || 'Task'}
                </h1>
              </div>
            </div>
          </header>

          {/* 可滚动内容区域 */}
          <div className="apt-scrollable-content">
            {/* 过滤器区域 */}
            <section className="apt-filters">
              <div className="progress-filters">
                <span className="filter-label">Risk Tiers:</span>
                {['Red', 'Orange', 'Yellow', 'Green'].map(tier => (
                  <button 
                    key={tier}
                    className={`filter-btn ${riskFilter.includes(tier) ? 'active' : ''}`}
                    onClick={() => toggleRiskFilter(tier)}
                    style={{
                      backgroundColor: riskFilter.includes(tier) ? getRiskColor(tier) : '#fff',
                      borderColor: getRiskColor(tier),
                      color: riskFilter.includes(tier) ? '#fff' : getRiskColor(tier)
                    }}
                  >
                    {tier}
                  </button>
                ))}
              </div>
              
              <div className="search-filter">
                <input
                  type="text"
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>
            </section>

            {/* 学生风险表格 */}
            <section className="apt-table-section">
              {filteredStudents.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-title">
                    {students.length === 0 ? 'No students found' : 'No students match your filters'}
                  </div>
                  <div className="empty-subtitle">
                    {students.length === 0 ? 'There are no students enrolled in this course.' : 'Try adjusting your filters or search term.'}
                  </div>
                </div>
              ) : (
                <div className="students-table">
                  <div className="table-header">
                    <div className="header-cell student-col">Student Name</div>
                    <div className="header-cell student-id-col">Student ID</div>
                    <div className="header-cell risk-col">Risk</div>
                    <div className="header-cell overdue-col">Overdue Parts</div>
                    <div className="header-cell action-col">Suggested Action</div>
                  </div>
                  
                  <div className="table-body">
                    {filteredStudents.map((student) => (
                      <div key={student.id} className="table-row">
                        <div className="cell student-col">
                          <div className="student-name">{student.name}</div>
                        </div>
                        <div className="cell student-id-col">
                          <div className="student-id">{student.studentId}</div>
                        </div>
                        <div className="cell risk-col">
                          <span 
                            className="risk-badge"
                            style={{ 
                              backgroundColor: getRiskColor(student.riskTier),
                              color: '#fff'
                            }}
                          >
                            {student.riskTier}
                          </span>
                        </div>
                        <div className="cell overdue-col">{student.overdueParts}</div>
                        <div className="cell action-col">{student.suggestedAction}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>

            {/* Tips区域 - 基于Figma设计 */}
            <section className="apt-tips-section">
              <div className="tips-header">
                <h3>Tips:</h3>
              </div>
              <div className="tips-content">
                <p><strong>Risk tiers:</strong> Red ≥5 overdue or &gt;5 consecutive; Orange 2–4 or 2–4; Yellow other non-Green cases (e.g., one overdue Part or 1 day not on time); Green never overdue & 0 consecutive.</p>
                <p>Counts are for this Course + Task; "Suggested action" is guidance only.</p>
              </div>
            </section>
          </div>
        </main>
      </div>

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

/* Risk Report页面样式 - 与AdminProgressTrend完全一致 */
const css = `
:root{
  --ah-border: #EAEAEA;
  --ah-muted: #6D6D78;
  --ah-text: #172239;
  --ah-card-bg:#FFFFFF;
  --ah-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --ah-primary: #BB87AC; /* 管理员紫色主题 */
  --ah-primary-light: rgba(187, 135, 172, 0.49); /* 半透明紫色 */
  
  /* 风险等级颜色 */
  --risk-red: #FF6B6B;
  --risk-orange: #FFA500;
  --risk-yellow: #FFD700;
  --risk-green: #4CAF50;
}

.admin-progress-trend-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:48px;
  padding:32px;
  color:var(--ah-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh;
}

/* 左侧导航栏样式 - 与AdminHome完全一致 */
.ah-sidebar{
  display:flex;
  flex-direction:column;
  gap:24px;
  height: 100%;
}

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
.ah-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--ah-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center;cursor:pointer;transition:background-color 0.2s}
.ah-profile-card .chevron:hover{background:var(--ah-primary-light)}

.ah-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
}
.ah-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ah-muted);text-decoration:none;font-weight:500;
  border: none;
  outline: none;
}
.ah-nav .item.active{background:var(--ah-primary);color:#172239;font-weight:600;border-radius:20px}
.ah-nav .nav-icon{width:20px;height:20px}

.ah-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-outline{
  padding:14px;
  border-radius:14px;
  background:#fff;
  border:1px solid var(--ah-border);
  cursor:pointer;
  font-weight:600;
  margin-top: auto;
}

/* 外层壳：与 Progress 完全一致 */
.apt-outer-container{
  background: var(--ah-card-bg);
  border: 1px solid var(--ah-border);
  border-radius: 20px;
  box-shadow: var(--ah-shadow);
  overflow: hidden;
  height: calc(100vh - 64px);
}

/* 右侧主内容：与 Progress 完全一致 */
.apt-main{
  display:flex;
  flex-direction:column;
  gap:32px;
  height: 100%;
  position: relative;
  padding: 24px;
  background: #f8f9fa;
}

/* 标题区（关键差异：margin-bottom 必须为 -16px） */
.apt-header{
  display:flex;
  align-items:flex-start;
  position: sticky;
  top: 0;
  background: #f8f9fa;
  z-index: 10;
  padding: 0 0 16px 0;
  margin-bottom: -16px; /* ← Progress 页就是 -16px，Risk 需一致 */
}

.header-content{
  display:flex;
  align-items:flex-start;
  gap:16px;
}

/* 标题文案样式统一（之前写成了 .arr-header 前缀，需切到 apt） */
.apt-header .left{ display:flex; flex-direction:column; gap:8px; }
.apt-header .hello{ font-size:32px; font-weight:600; color:var(--ah-text); }
.apt-header .title{ font-size:18px; font-weight:400; color:var(--ah-muted); margin:0; }

/* 可滚动内容区：与 Progress 完全一致 */
.apt-scrollable-content{
  display:flex;
  flex-direction:column;
  gap:32px;
  overflow-y: auto;
  padding-right: 8px;
  flex: 1;
}

.apt-header .left{
  display:flex;flex-direction:column;
  gap:8px;
}
.apt-header .hello{
  font-size:32px;font-weight:600;
  color:var(--ah-text);
}
.apt-header .title{
  font-size:18px;font-weight:400;
  color:var(--ah-muted);
  margin:0;
}

/* 返回按钮样式 - 与Admin Progress Trend页面一致 */
.cd-hero-clean{
  position: relative;
  text-align: left;
  padding: 4px 0 8px;
  margin-bottom: 6px;
  background: transparent;
  display: flex;
  align-items: flex-start;
}

.back-circle{
  padding: 8px;
  border: 1px solid var(--ah-border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.back-circle:hover{
  background: var(--ah-primary-light);
  border-color: var(--ah-primary);
}

.chev-left{
  transform: rotate(180deg);
}

/* 过滤器区域 */
.apt-filters{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:24px;
  padding:20px;
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
}

.progress-filters{
  display:flex;
  align-items:center;
  gap:12px;
  flex-wrap:wrap;
}

.filter-label{
  font-weight:600;
  color:var(--ah-text);
  white-space:nowrap;
}

.filter-btn{
  padding:8px 16px;
  border-radius:6px;
  background:#fff;
  cursor:pointer;
  font-size:14px;
  transition:all 0.2s ease;
  border: 1px solid;
}

.filter-btn:hover{
  opacity: 0.8;
}

.filter-btn.active{
  color:white;
}

.search-input{
  padding:8px 12px;
  border:1px solid var(--ah-border);
  border-radius:6px;
  font-size:14px;
  min-width:200px;
}

/* 学生风险表格 */
.apt-table-section{
  flex:1;
}

.empty-state{
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  height:200px;text-align:center;
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
}
.empty-state .empty-title{
  font-size:18px;font-weight:600;
  color:var(--ah-text);
  margin-bottom:8px;
}
.empty-state .empty-subtitle{
  font-size:14px;color:var(--ah-muted);
}

.students-table{
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
  overflow:hidden;
}

.table-header{
  display:grid;
  grid-template-columns:1.5fr 1fr 1fr 1fr 1.5fr;
  gap:1px;
  background:var(--ah-border);
}

.header-cell{
  padding:16px 20px;
  background:var(--ah-primary);
  color:white;
  font-weight:600;
  font-size:14px;
  text-align:center;
}

.table-body{
  display:flex;
  flex-direction:column;
}

.table-row{
  display:grid;
  grid-template-columns:1.5fr 1fr 1fr 1fr 1.5fr;
  gap:1px;
  background:var(--ah-border);
  transition:background 0.2s ease;
}

.table-row:hover{
  background:var(--ah-primary-light);
}

.cell{
  padding:16px 20px;
  background:white;
  font-size:14px;
  display:flex;
  align-items:center;
}

/* 统一表格五列字体样式 - 与AdminProgressTrend完全一致 */
.students-table .cell {
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: var(--ah-text); /* 黑色字体 */
}

/* 只保留对齐方式差异 */
.students-table .student-col {
  justify-content: flex-start;
}

.students-table .student-id-col,
.students-table .risk-col,
.students-table .overdue-col {
  justify-content: center;
}

.students-table .action-col {
  justify-content: center;
}

/* 风险徽章样式 */
.risk-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

/* Tips区域样式 */
.apt-tips-section{
  background:var(--ah-card-bg);
  border-radius:12px;
  border:1px solid var(--ah-border);
  padding:24px;
}

.tips-header{
  margin-bottom:16px;
}

.tips-header h3{
  margin:0;
  font-size:18px;
  font-weight:600;
  color:var(--ah-text);
}

.tips-content{
  font-size:14px;
  color:var(--ah-muted);
  line-height:1.6;
}

.tips-content p{
  margin:8px 0;
}

.tips-content strong{
  color:var(--ah-text);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .admin-progress-trend-layout{
    grid-template-columns: 240px 1fr;
  }
}

@media (max-width: 768px) {
  .admin-progress-trend-layout{
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
  
  .ah-sidebar{
    order: 2;
  }
  
  .apt-main{
    max-height: none;
    overflow-y: visible;
  }
  
  .table-header,
  .table-row{
    grid-template-columns:1fr 1fr 1fr 1fr 1fr;
    gap:1px;
  }
  
  .header-cell,
  .cell{
    padding:12px 16px;
  }
  
  .apt-filters{
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .progress-filters{
    justify-content: center;
  }
}
`