import { useEffect, useState } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import IconRisk from '../../assets/icons/help-24.svg'
import apiService from '../../services/api'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import illustrationAdmin from '../../assets/images/illustration-admin.png'
import illustrationAdmin2 from '../../assets/images/illustration-admin2.png'
import illustrationAdmin3 from '../../assets/images/illustration-admin3.png'
import illustrationAdmin4 from '../../assets/images/illustration-admin4.png'

import { courseAdmin } from '../../store/coursesAdmin';


// 图片映射 - 循环使用4张图片
const adminIllustrations = [
  illustrationAdmin,
  illustrationAdmin2, 
  illustrationAdmin3,
  illustrationAdmin4
];

export function AdminHome() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [courses, setCourses] = useState(courseAdmin.all)
  const uid = localStorage.getItem('current_user_id') || '';
  const [user, setUser] = useState<{ name?: string; email?: string; avatarUrl?: string } | null>(() => {
    if (!uid) return null;
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'); }
    catch { return null; }
  });
  
  //4个数量展示
  const [stats, setStats] = useState({
      totalCourses: 0,
      totalStudents: 0,
      activeTasks: 0,
      atRiskStudents: 0
    })
  
  // ============================================
  // 🚨 MOCK DATA SECTION - 管理员创建的课程数据 🚨
  // ============================================
  // TODO: 这里需要替换为真实的后端API调用
  // 从localStorage读取管理员创建的课程数据
  // ============================================
  
  //展示创建的课程 
  const [createdCourses, setCreatedCourses] = useState<Array<{
  id: string;
  title: string;
  desc: string;
  illustrationIndex: number;
  studentCount?: number; 
}>>(() => {
  try {
    const adminId = localStorage.getItem('current_user_id');
    const saved = adminId
      ? localStorage.getItem(`admin:${adminId}:courses`)
      : null;
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
});

  useEffect(() => {
    if (uid) {
      try {
        setUser(JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'));
      } catch {
        setUser(null);
      }
    } else {
      setUser(null);
    }

    const unsubCourses = courseAdmin.subscribe(() => {
    setCourses([...courseAdmin.all]);
  });

    (async () => {
    await courseAdmin.getMyCourses();     // 先等课程
    await courseAdmin.getMyTasks();       // 再拉任务
    await courseAdmin.getMyMaterials();   // 再拉材料
    await courseAdmin.getMyQuestions();   // 再拉question
  })();
  
    // 监听localStorage变化来更新课程数据
    const handleStorageChange = () => {
      try {
        const adminId = localStorage.getItem('current_user_id');
        if (!adminId) return;

        const saved = localStorage.getItem(`admin:${adminId}:courses`);
        if (saved) {
          setCreatedCourses(JSON.parse(saved));
        } else {
          setCreatedCourses([]);
        }
      } catch {
        setCreatedCourses([]);
      }
    };

    // 添加storage事件监听器
    window.addEventListener('storage', handleStorageChange);

    // 更新统计数据
    const totalCreatedCourses = createdCourses.length;
    
    const totalStudents = createdCourses.reduce(
    (sum, c) => sum + (c.studentCount ?? 0),
    0
  );


    let totalTasks = 0;
    const adminId = localStorage.getItem('current_user_id');
    // 直接读取总任务数
    const savedTotal = localStorage.getItem(`admin:${adminId}:tasks_total_count`);
    if (savedTotal) {
      totalTasks = Number(savedTotal);
    } else {
      const countsByCourse = JSON.parse(
        localStorage.getItem(`admin:${adminId}:tasks_counts_by_course`) || '{}'
      );
      totalTasks = Object.values(countsByCourse).reduce(
        (sum: number, n: any) => sum + Number(n),
        0
      );
    }
    setStats({
      totalCourses: totalCreatedCourses,
      totalStudents: totalStudents,
      activeTasks: totalTasks,
      atRiskStudents: 0
    });

    return () => {
      unsubCourses();
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [uid]);
  useEffect(() => {
    if (!uid) return;
    if (courseAdmin.all.length === 0) {
  }
  }, [uid]);

  // 监听createdCourses变化，实时更新统计数据
  useEffect(() => {
    setStats(prev => ({
      ...prev,
      totalCourses: createdCourses.length
    }));
  }, [createdCourses]);

  // 统计Risk Student数量（橙色和红色学生）
  useEffect(() => {
    const calculateRiskStudents = () => {
      try {
        // 从localStorage获取所有课程的风险学生数据
        const adminId = localStorage.getItem('current_user_id');
        if (!adminId) return 0;

        // 获取管理员创建的所有课程
        const savedCourses = localStorage.getItem(`admin:${adminId}:courses`);
        if (!savedCourses) return 0;

        const courses = JSON.parse(savedCourses);
        let totalRiskStudents = 0;

        // 遍历所有课程，统计风险学生
        courses.forEach((course: any) => {
          if (course.students && Array.isArray(course.students)) {
            // 统计橙色和红色的学生
            const riskStudents = course.students.filter((student: any) => 
              student.riskTier === 'Orange' || student.riskTier === 'Red'
            );
            totalRiskStudents += riskStudents.length;
          }
        });

        return totalRiskStudents;
      } catch (error) {
        console.error('Error calculating risk students:', error);
        return 0;
      }
    };

    // 更新统计数据
    setStats(prev => ({
      ...prev,
      atRiskStudents: calculateRiskStudents()
    }));
  }, [uid, createdCourses]);

  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
    try { await apiService.logout_adm(); }
    finally {
      window.location.hash = '#/login-admin';
      setLogoutModalOpen(false);
    }
  };

  return (
    <div key={uid} className="admin-home-layout">
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
          <a className="item active" href="#/admin-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/admin-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item" href="#/admin-monitor">
            <img src={IconMonitor} className="nav-icon" alt="" /> Analytics
          </a>
        </nav>

        <div className="ah-illustration">
          <img src={adminHomepageImage} alt="Admin Dashboard" style={{ width: '100%', height: 'auto', borderRadius: '20px' }} />
        </div>

        <button className="btn-outline" onClick={handleLogout}>Log Out</button>
      </aside>

      <main className="ah-main">
        <header className="ah-header">
          <div className="left">
            <div className="hello">Hello,</div>
            <h1 className="title">{user?.name || 'Admin'} <span className="wave" aria-hidden>👋</span></h1>
          </div>
        </header>

        {/* 统计卡片区域 */}
        <section className="ah-stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.totalCourses}</div>
              <div className="stat-label">Total Courses</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.totalStudents}</div>
              <div className="stat-label">Total Students</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.activeTasks}</div>
              <div className="stat-label">Active Tasks</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.atRiskStudents}</div>
              <div className="stat-label">At-risk students</div>
            </div>
          </div>
        </section>

        {/* 课程区域 */}
        <section className="ah-courses-section">
          <div className="section-title">Courses <span aria-hidden>😉</span></div>

          {createdCourses.length === 0 ? (
            <div className="courses-empty">
              <div className="title">No Courses found yet.</div>
              <div className="sub">Go to 'My Courses' to create course</div>
            </div>
          ) : (
            <div className="courses-grid">
              {createdCourses.map((course) => (
                <div 
                  key={course.id} 
                  className="course-card"
                  onClick={() => window.location.hash = `#/admin-manage-course?courseId=${course.id}`}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="course-thumb">
                    <img src={adminIllustrations[course.illustrationIndex]} alt="" />
                  </div>
                  <div className="course-info">
                    <h3 className="course-id">{course.id}</h3>
                    <p className="course-title">{course.title}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
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

/* 管理员主页样式 - 紫色主题 */
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

.admin-home-layout{
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

/* 侧栏-用户卡 */
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

/* 侧栏-导航 */
.ah-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
}
.ah-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ah-muted);text-decoration:none;font-weight:500;
}
.ah-nav .item.active{background:var(--ah-primary);color:#172239;font-weight:600;border-radius:20px}
.ah-nav .nav-icon{width:20px;height:20px}

/* 侧栏-插图 */
.ah-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-outline{
  padding:14px;border-radius:14px;background:#fff;border:1px solid var(--ah-border);cursor:pointer;font-weight:600;
  margin-top: auto;
}

/* 主内容区域 */
.ah-main{
  display:flex;
  flex-direction:column;
  min-height:100%;
  overflow:hidden; /* 右侧容器不滚动 */
}

/* 顶部标题 */
.ah-header{display:flex;align-items:center;justify-content:space-between}
.ah-header .hello{color:var(--ah-muted);font-size:20px}
.ah-header .title{font-size:40px;line-height:1.2;margin:4px 0 0;font-weight:600}
.ah-header .right{display:flex;align-items:center;gap:12px}
.ah-header .icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--ah-border);background:#fff;display:grid;place-items:center}

/* 统计卡片区域 */
.ah-stats-section{
  margin-top: 16px;
}

.stats-grid{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card{
  background: var(--ah-primary-light);
  border: 1px solid var(--ah-border);
  border-radius: 20px;
  padding: 32px;
  text-align: center;
  box-shadow: var(--ah-shadow);
  width: 197.66px;
  height: 168.86px;
}

.stat-value{
  font-size: 40px;
  font-weight: 700;
  color: var(--ah-text);
  margin-bottom: 8px;
}

.stat-label{
  font-size: 20px;
  font-weight: 400;
  color: var(--ah-text);
}

/* 课程区域 */
.ah-courses-section{
  margin-top: 16px;
}

.section-title{
  font-weight:600;
  margin-bottom:20px;
  font-size:40px;
}

.courses-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));
  gap:20px;
}

.course-card{
  display:flex;
  flex-direction:column;
  width:100%;
  border:1px solid var(--ah-border);
  border-radius:32px;
  background:#fff;
  box-shadow:var(--ah-shadow);
  padding:0;
  overflow:hidden;
  cursor:pointer;
  transition: all 0.2s ease;
  min-height: 280px; /* 移除description后可以更紧凑 */
}

.course-card:hover{
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.course-card .course-thumb{
  width:100%;
  height:137px;
  border-top-left-radius: 32px;
  border-top-right-radius: 32px;
  display: flex;
  align-items: flex-start; /* 图片从顶部开始显示 */
  justify-content: center;
  overflow: hidden;
}

.course-card .course-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 图片拉伸填充整个区域 */
  object-position: top; /* 图片顶部对齐，只显示上半部分 */
}

.course-card .course-info{
  flex:1;
  padding: 16px 24px 24px 24px; /* 上边距减少，让内容更靠近图片 */
  display: flex;
  flex-direction: column;
  gap: 8px; /* 减少间距 */
  justify-content: flex-start; /* 内容从顶部开始 */
  min-height: 100px; /* 进一步减少高度 */
}

.course-card .course-id{
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--ah-text);
  line-height: 1.2;
}

.course-card .course-title{
  font-size: 14px;
  color: var(--ah-muted);
  margin: 0;
  font-weight: 500;
}

.course-card .course-description{
  font-size: 14px;
  color: var(--ah-muted);
  margin: 0;
  line-height: 1.5;
}

.courses-empty{
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:8px;
  padding:150px;
  border:none;
  border-radius:0;
  background:transparent;
  color:var(--ah-muted);
}

.courses-empty .title{
  font-weight:800;
  font-size:32px;
  color:#172239;
  margin-bottom: 12px;
}

.courses-empty .sub{
  font-size:24px;
  font-weight: 300;
}



@media (max-width: 1200px){
  .admin-home-layout{
    grid-template-columns: 240px 1fr;
  }
  
  .stats-grid{
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px){
  .admin-home-layout{
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
  
  .stats-grid{
    grid-template-columns: 1fr;
  }
  
  .ah-sidebar{
    order: 2;
  }
  
  .ah-main{
    order: 1;
  }
}
`