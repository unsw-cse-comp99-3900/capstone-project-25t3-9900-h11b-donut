import { useState, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconMonitor from '../../assets/icons/bell-24.svg'
import IconRisk from '../../assets/icons/help-24.svg'
import IconSearch from '../../assets/icons/search-24.svg'
import adminHomepageImage from '../../assets/images/admin-homepage.png'
import illustrationAdmin from '../../assets/images/illustration-admin.png'
import illustrationAdmin2 from '../../assets/images/illustration-admin2.png'
import illustrationAdmin3 from '../../assets/images/illustration-admin3.png'
import illustrationAdmin4 from '../../assets/images/illustration-admin4.png'
import apiService from '../../services/api'
import { courseAdmin } from '../../store/coursesAdmin'

// 图片映射 - 循环使用4张图片
const adminIllustrations = [
  illustrationAdmin,
  illustrationAdmin2, 
  illustrationAdmin3,
  illustrationAdmin4
];

export function AdminCourses() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [courses, setCourses] = useState(courseAdmin.all)
  const [creating, setCreating] = useState(false);
  const [createCourseModalOpen, setCreateCourseModalOpen] = useState(false)
  const [courseId, setCourseId] = useState('')
  const [courseName, setCourseName] = useState('')
  const [courseDescription, setCourseDescription] = useState('')
  
  const [createdCourses, setCreatedCourses] = useState<Array<{
  id: string;
  title: string;
  description: string;
  illustrationIndex: number;
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

  // 删除课程函数
  const handleDeleteCourse = async(courseId: string) => {
    const snapshot = createdCourses;

    setCreatedCourses(prev => {
      const updated = prev.filter(course => course.id !== courseId);
      const adminId = localStorage.getItem('current_user_id');
      if (adminId) {
      localStorage.setItem(`admin:${adminId}:courses`, JSON.stringify(updated));
    }
      return updated;
    });
    try {
    await apiService.adminDeleteCourse(courseId); 
    } catch (e) {
      // 失败回滚
      setCreatedCourses(snapshot);
      const adminId = localStorage.getItem('current_user_id');
      if (adminId) {
        localStorage.setItem(`admin:${adminId}:courses`, JSON.stringify(snapshot));
      }
      alert('fail!!!');
    }
  };
  
  const uid = localStorage.getItem('current_user_id') || '';
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
    const unsubCourses = courseAdmin.subscribe(() => {
    setCourses([...courseAdmin.all]);
  });

    return () => {
      unsubCourses();
    };
  }, [uid]);

  
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

  const handleCreateNewCourse = () => {
    setCreateCourseModalOpen(true);
  };

  const handleCloseCreateCourseModal = () => {
    setCreateCourseModalOpen(false);
    setCourseId('');
    setCourseName('');
    setCourseDescription('');
  };

  // Course ID格式化函数 - 前四个字母自动转为大写
  const formatCourseId = (input: string): string => {
    if (input.length <= 4) {
      return input.toUpperCase();
    }
    return input.substring(0, 4).toUpperCase() + input.substring(4);
  };

  // Course Name格式化函数 - 每个单词首字母大写
  const formatCourseName = (input: string): string => {
    return input
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const handleSubmitCreateCourse = async() => {
    if (creating) return; 
    // 验证必填字段
    if (!courseId.trim()) { alert('Please enter Course ID'); return; }
    if (!courseName.trim()) { alert('Please enter Course Name'); return; }
    
    // 格式化输入数据
    const formattedCourseId = formatCourseId(courseId);
    const formattedCourseName = formatCourseName(courseName);
    
    // 计算图片索引 - 循环使用4张图片
    const illustrationIndex = createdCourses.length % 4;
    
    const check = await apiService.adminCheckCourseExists(formattedCourseId);
    console.log(check.data.exists)
    if (check?.data?.exists) {
      alert('This Course ID already exists in database.');
      return;
    }
    const illustrations: Array<'orange' | 'student' | 'admin'> = ['orange', 'student', 'admin'];
    const illustration = illustrations[createdCourses.length % illustrations.length];
    // 创建新课程
    const newCourse = {
      id: formattedCourseId,
      title: formattedCourseName,
      description: courseDescription,
      illustrationIndex: illustrationIndex
    };
    
    const adminId = localStorage.getItem('current_user_id');
    const snapshot = createdCourses;

    // 添加到已创建课程列表并保存到localStorage
   
    try {
    await apiService.adminCreateCourse({
      code: formattedCourseId,
      title: formattedCourseName,
      description: courseDescription,
      illustration,
    });
    setCreatedCourses(prev => {
        const updated = [...prev, newCourse];
        if (adminId) localStorage.setItem(`admin:${adminId}:courses`, JSON.stringify(updated));
        return updated;
      });
    handleCloseCreateCourseModal();
  } catch (e: any) {
    // 失败回滚本地
    alert(`创建失败：${e?.message || 'Please try again'}`);
    setCreatedCourses(snapshot);
    if (adminId) localStorage.setItem(`admin:${adminId}:courses`, JSON.stringify(snapshot));
  }
  };

  return (
    <div key={uid} className="admin-courses-layout">
      {/* 左侧导航栏 - 与AdminHome保持一致 */}
      <aside className="ac-sidebar">
        <div className="ac-profile-card">
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

        <nav className="ac-nav">
          <a className="item" href="#/admin-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item active" href="#/admin-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item" href="#/admin-monitor">
            <img src={IconMonitor} className="nav-icon" alt="" /> Analytics
          </a>
        </nav>

        <div className="ac-illustration">
          <img src={adminHomepageImage} alt="Admin Dashboard" style={{ width: '100%', height: 'auto', borderRadius: '20px' }} />
        </div>

        <button className="btn-outline" onClick={handleLogout}>Log Out</button>
      </aside>

      {/* 右侧主内容区域 */}
      <main className="ac-main">
        <header className="ac-header">
          <div className="left">
            <h1 className="title">Courses 📖</h1>
          </div>
          <div className="right">
            <button className="create-course-btn" onClick={handleCreateNewCourse}>
              + Create New Course
            </button>
          </div>
        </header>

        {/* 课程内容区域 */}
        <section className="ac-content">
          {courses.length === 0 && createdCourses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-container">
                <div className="empty-message">You don't have any course yet!</div>
              </div>
            </div>
          ) : (
            <div className="courses-grid">
              {/* 显示已创建的课程 */}
              {createdCourses.map((course) => (
                <div key={course.id} className="course-card">
                  <div className="course-thumb">
                    <img src={adminIllustrations[course.illustrationIndex]} alt="" />
                  </div>
                  <div className="course-info">
                    <h3 className="course-id">{course.id}</h3>
                    <p className="course-title">{course.title}</p>
                    <p className="course-description">
                      {course.description || '    '}
                    </p>
                  </div>
                  <div className="course-actions">
                    <button 
                      className="manage-btn"
                      onClick={() => window.location.hash = `#/admin-manage-course?courseId=${course.id}`}
                    >
                      Manage
                    </button>
                    <button 
                      className="delete-btn"
                      onClick={() => handleDeleteCourse(course.id)}
                    >
                      Delete
                    </button>
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

      {/* 创建课程弹窗 */}
      {createCourseModalOpen && (
        <div className="modal-overlay">
          <div className="create-course-modal">
            <div className="modal-header">
              <button className="modal-close" onClick={handleCloseCreateCourseModal} aria-label="Close">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <h2 className="modal-title">New Course</h2>
            </div>
            <div className="modal-content">
              <div className="form-group">
                <label className="form-label">Course ID:</label>
                <input
                  type="text"
                  className="form-input"
                  value={courseId}
                  onChange={(e) => setCourseId(formatCourseId(e.target.value))}
                  placeholder="Enter course ID"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Course Name:</label>
                <input
                  type="text"
                  className="form-input"
                  value={courseName}
                  onChange={(e) => setCourseName(formatCourseName(e.target.value))}
                  placeholder="Enter course name"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description (optional):</label>
                <textarea
                  className="form-textarea"
                  value={courseDescription}
                  onChange={(e) => setCourseDescription(e.target.value)}
                  placeholder="Enter course description"
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="modal-button add" onClick={handleSubmitCreateCourse}>
                Add
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{css}</style>
    </div>
  )
}

/* Admin My Courses 页面样式 */
const css = `
:root{
  --ac-border: #EAEAEA;
  --ac-muted: #6D6D78;
  --ac-text: #172239;
  --ac-card-bg:#FFFFFF;
  --ac-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --ac-primary: #BB87AC; /* 管理员紫色主题 */
  --ac-primary-light: rgba(187, 135, 172, 0.49); /* 半透明紫色 */
  --ac-create-btn: #2673DD; /* 创建按钮蓝色 */
}

.admin-courses-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:48px;
  padding:32px;
  color:var(--ac-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  font-size: 16px;
  min-height: 100vh;
}

.ac-sidebar{
  display:flex;
  flex-direction:column;
  gap:24px;
  height: 100%;
}

/* 侧栏-用户卡 */
.ac-profile-card{
  display:flex;align-items:center;gap:12px;
  padding:16px;border:1px solid var(--ac-border);border-radius:20px;background:var(--ac-card-bg);box-shadow:var(--ac-shadow);
  height: 95.36px;
}
.ac-profile-card .avatar{
  width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--ac-border);
}
.ac-profile-card .info .name{font-size:16px;font-weight:600}
.ac-profile-card .info .email{color:var(--ac-muted);font-size:12px}
.ac-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--ac-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center;cursor:pointer;transition:background-color 0.2s}
.ac-profile-card .chevron:hover{background:var(--ac-primary-light)}

/* 侧栏-导航 */
.ac-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--ac-border);border-radius:20px;background:#fff;box-shadow:var(--ac-shadow);
}
.ac-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ac-muted);text-decoration:none;font-weight:500;
}
.ac-nav .item.active{background:var(--ac-primary);color:#172239;font-weight:600;border-radius:20px}
.ac-nav .nav-icon{width:20px;height:20px}

/* 侧栏-插图 */
.ac-illustration{
  margin-top: auto;
  margin-bottom: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-outline{
  padding:14px;border-radius:14px;background:#fff;border:1px solid var(--ac-border);cursor:pointer;font-weight:600;
  margin-top: auto;
}

/* 主内容区域 */
.ac-main{
  display:flex;
  flex-direction:column;
  min-height:100%;
  overflow:hidden;
}

/* 顶部标题区域 */
.ac-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom: 40px;
}

.ac-header .title{
  font-size:24px;
  font-weight:600;
  margin:0;
}

.ac-header .right{
  display:flex;
  align-items:center;
  gap:20px;
}

/* 搜索框 */
.search-container{
  display:flex;
  align-items:center;
  gap:12px;
  padding:12px 16px;
  border:1px solid var(--ac-border);
  border-radius:16px;
  background:#fff;
  width:326px;
  height:48px;
}

.search-input{
  border:none;
  outline:none;
  font-size:14px;
  font-weight:400;
  color:var(--ac-muted);
  width:100%;
  background:transparent;
}

.search-input::placeholder{
  color:var(--ac-muted);
}

/* 创建课程按钮 */
.create-course-btn{
  background: rgba(187, 135, 172, 0.9); /* BB87AC紫色，90%透明度 */
  color:white;
  border:none;
  border-radius:12px;
  padding:16px 24px;
  font-size:20px;
  font-weight:700;
  cursor:pointer;
  height:63px;
  width:259px;
  display:flex;
  align-items:center;
  justify-content:center;
  transition:background-color 0.2s ease;
}

.create-course-btn:hover{
  background: rgba(187, 135, 172, 1); /* 悬停时完全不透明 */
}

/* 内容区域 */
.ac-content{
  flex:1;
  display:flex;
  flex-direction:column;
}

/* 空状态 */
.empty-state{
  flex:1;
  display:flex;
  align-items:center;
  justify-content:center;
}

.empty-container{
  text-align:center;
}

.empty-message{
  font-size:24px;
  font-weight:600;
  color:var(--ac-text);
  margin:0;
}

/* 课程网格 */
.courses-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));
  gap:24px;
  padding:20px 0;
}

/* 课程卡片 */
.course-card{
  border:1px solid var(--ac-border);
  border-radius:32px;
  background:#fff;
  box-shadow:var(--ac-shadow);
  display:flex;
  flex-direction:column;
  overflow: hidden;
  min-height: 320px; /* 固定最小高度，确保卡片大小一致 */
  cursor: pointer;
  transition: all 0.2s ease;
}

.course-card:hover{
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}

.course-thumb {
  width: 100%;
  height: 137px;
  border-top-left-radius: 32px;
  border-top-right-radius: 32px;
  display: flex;
  align-items: flex-start; /* 图片从顶部开始显示 */
  justify-content: center;
  overflow: hidden;
}

.course-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 图片拉伸填充整个区域 */
  object-position: top; /* 图片顶部对齐，只显示上半部分 */
}

.course-info{
  flex:1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.course-id{
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--ac-text);
  line-height: 1.2;
}

.course-title{
  font-size: 14px;
  color: var(--ac-muted);
  margin: 0;
  font-weight: 500;
}

.course-description{
  font-size: 14px;
  color: var(--ac-muted);
  margin: 0;
  line-height: 1.5;
  flex: 1;
}

.course-actions {
  display: flex;
  gap: 12px;
  margin: 0 24px 24px 24px;
}

.manage-btn{
  background: var(--ac-primary);
  color: var(--ac-text);
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  flex: 1;
  transition: background-color 0.2s ease;
}

.manage-btn:hover{
  background: #a57598;
}

.delete-btn{
  background: #FF6B6B;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  flex: 1;
  transition: background-color 0.2s ease;
}

.delete-btn:hover{
  background: #FF5252;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .admin-courses-layout{
    grid-template-columns:1fr;
    gap:24px;
    padding:16px;
  }
  
  .ac-sidebar{
    order:2;
  }
  
  .ac-header{
    flex-direction:column;
    gap:16px;
    align-items:flex-start;
  }
  
  .ac-header .right{
    width:100%;
    justify-content:space-between;
  }
  
  .search-container{
    width:200px;
  }
  
  .create-course-btn{
    width:200px;
    font-size:16px;
  }
}

@media (max-width: 768px) {
  .courses-grid{
    grid-template-columns:1fr;
  }
  
  .ac-header .right{
    flex-direction:column;
    gap:12px;
  }
  
  .search-container{
    width:100%;
  }
  
  .create-course-btn{
    width:100%;
  }
}

/* 创建课程弹窗样式 - 采用preference弹窗设计，紫色主题 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: saturate(180%) blur(2px);
  z-index: 1000;
  will-change: transform;
}

.create-course-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 520px;
  max-width: 92vw;
  background: #fff;
  border-radius: 20px;
  border: 2px solid #BB87AC; /* 紫色边框，类似preference弹窗 */
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12);
  padding: 28px;
  z-index: 1010;
  will-change: transform;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  position: relative;
  padding: 32px 32px 24px;
  border-bottom: 1px solid #EAEAEA;
  flex-shrink: 0;
}

.modal-title {
  text-align: center;
  font-weight: 800;
  font-size: 22px;
  margin: 4px 0 16px;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.modal-close {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--sh-border, #D0D5DD);
  background: #fff;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #6D6D78;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #BB87AC; /* 紫色背景 */
  border-color: #BB87AC;
  color: white;
}

.modal-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 16px;
  font-weight: 600;
  color: #172239;
  font-family: 'Montserrat', sans-serif;
}

.form-input, .form-textarea {
  padding: 12px 16px;
  border: 1px solid #D0D5DD;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Montserrat', sans-serif;
  background: white;
  transition: border-color 0.2s ease;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #BB87AC; /* 紫色焦点边框 */
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 32px;
  border-top: 1px solid #EAEAEA;
}

.modal-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Montserrat', sans-serif;
  transition: all 0.2s ease;
  min-width: 120px;
}

.modal-button.cancel {
  background: #F8F9FA;
  color: #6D6D78;
  border: 1px solid #D0D5DD;
}

.modal-button.cancel:hover {
  background: #F0F2F7;
}

.modal-button.add {
  background: #BB87AC;
  color: white;
}

.modal-button.add:hover {
  background: #A57598;
}
`