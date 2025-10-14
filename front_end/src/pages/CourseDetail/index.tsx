import { useState, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'

import illoOrange from '../../assets/images/illustration-orange.png'
import illoStudent from '../../assets/images/illustration-student.png'
import illoAdmin from '../../assets/images/illustration-admin.png'


import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import UserWhite from '../../assets/icons/user-24-white.svg'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import { coursesStore, type Task } from '../../store/coursesStore'
import type { Course } from '../../store/coursesStore'
import { DownloadButton } from '../../components/DownloadButton'
import { apiService } from '../../services/api'



interface Material {
  id: string
  title: string
  fileType: string
  fileSize: string
  description: string
  uploadDate: string
}

interface CourseDetailData {
  tasks: Task[]
  materials: Material[]
}

/* 数据来源统一到 coursesStore：任务使用 coursesStore.getCourseTasks，材料此处留空或后续扩展 */

const illoMap: Record<'orange' | 'student' | 'admin', string> = {
  orange: illoOrange,
  student: illoStudent,
  admin: illoAdmin,
}

export function CourseDetail() {
  const [course, setCourse] = useState<Course | null>(null)
  const [detailData, setDetailData] = useState<CourseDetailData | null>(null)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [courseProgress, setCourseProgress] = useState(0)
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const handleDownload = async (materialId: string) => {
    try {
      const blob = await apiService.downloadMaterial(materialId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'material' // 简化文件名，实际项目中可以从material对象获取
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download failed, please try again later')
    }
  }


  useEffect(() => {
    // 从 URL 获取课程 ID
    const hash = window.location.hash
    const match = hash.match(/#\/course-detail\/(.+)/)
    if (match) {
      const id = match[1]
      
      // 查找课程信息
      const foundCourse = coursesStore.availableCourses.find(c => c.id === id)
      setCourse(foundCourse || null)
      
      // 获取课程详情数据：任务统一从 coursesStore 获取，材料从API获取
      const loadCourseData = async () => {
        try {
          const materials = await apiService.getCourseMaterials(id)
          const data = { 
            tasks: await coursesStore.getCourseTasksAsync(id), 
            materials 
          }
          setDetailData(data)
        } catch (error) {
          console.error('Failed to load materials:', error)
          // 如果API失败，使用空材料列表
          const data = { 
            tasks: await coursesStore.getCourseTasksAsync(id), 
            materials: [] 
          }
          setDetailData(data)
        }
      }
      
      loadCourseData()
      
      // 计算课程整体进度
      const progress = coursesStore.getCourseProgress(id)
      setCourseProgress(progress)
    }
  }, [])

  if (!course) {
    return (
      <div className="course-detail-layout">
        <div className="loading">Course not found</div>
      </div>
    )
  }

  return (
    <div className="course-detail-layout">
      {/* Left: 与 StudentHome 一致 */}
      <aside className="sh-sidebar">
        <div
          className="sh-profile-card"
          onClick={() => (window.location.hash = '#/student-profile')}
          role="button"
          aria-label="Open profile"
          style={{ cursor: 'pointer' }}
        >
          <div className="avatar"><img
    src={user?.avatarUrl || AvatarIcon}
    width={48}
    height={48}
    alt="avatar"
    style={{ borderRadius: '50%', objectFit: 'cover' }}
    onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
  /></div>
          <div className="info">
            <div className="name">{user.name}</div>
            <div className="studentId">{user.studentId}</div>
          </div>
          <button className="chevron" aria-label="Profile">
            <img src={ArrowRight} width={16} height={16} alt="" />
          </button>
        </div>

        <nav className="sh-nav">
          <a className="item" href="#/student-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/student-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item" href="#/student-plan">
            <img src={IconSettings} className="nav-icon" alt="" /> My plan
          </a>
        </nav>

        <div className="sh-ai-card">
          <div className="ai-icon"><img src={UserWhite} width={24} height={24} alt="" /></div>
          <div className="ai-title">AI Coach</div>
          <div className="ai-sub">Chat with your AI Coach!</div>
          <button className="btn-primary ghost ai-start">
            <span className="spc"></span>
            <span className="label">Start Chat</span>
            <img src={ArrowRight} width={16} height={16} alt="" className="chev" />
          </button>
        </div>

        <button className="btn-outline" onClick={() => setShowLogoutConfirm(true)}>Log Out</button>
      </aside>

      {/* Middle: 课程详情 */}
      <main className="cd-main">
        

        <div className="sc-board">
          <div className="courses-grid">
            <div className="course-card course-detail-card">
              {/* Clean hero: horizontal row — image + title on the right of back button */}
              <div className="cd-hero-clean">
                <button
                  className="back-circle"
                  aria-label="Back to courses"
                  onClick={() => (window.location.hash = '#/student-courses')}
                >
                  <img src={ArrowRight} width={16} height={16} alt="" className="chev-left" />
                </button>

                <div className="course-meta-row">
                  <div className="course-illustration">
                    <img src={illoMap[course.illustration]} alt="" />
                  </div>
                  <div className="course-title-section">
                    <h1 className="course-title">{course.id}</h1>
                    <p className="course-subtitle">{course.desc}</p>
                    <div className="course-overall-progress">
                      <div className="progress-label">Overall Progress</div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${courseProgress}%` }}></div>
                      </div>
                      <div className="progress-percent">{courseProgress}%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Scrollable content area */}
              <div className="course-detail-content">
                <div className="cd-sections">
                  {/* Task List */}
                  <div className="cd-section">
                    <h2>Task Lists</h2>
                    {detailData?.tasks.length ? (
                      <div className="task-list">
                        {detailData.tasks.map(task => (
                          <div key={task.id} className="task-item">
                            <div className="task-info">
                              <h3>{task.title}</h3>
                              <p>{task.brief}</p>
                              <div className="task-meta">
                                <span className="meta-chip">Course ID: {course.id}</span>
                                <span className="meta-chip">Task ID: {task.id}</span>
                              </div>
                              <span className="deadline">Deadline: {task.deadline}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state">
                        <p>No tasks yet</p>
                      </div>
                    )}
                  </div>

                  {/* Learning Materials */}
                  <div className="cd-section">
                    <h2>Learning Materials</h2>
                    {detailData?.materials.length ? (
                      <div className="material-list">
                        {detailData.materials.map(material => (
                          <div key={material.id} className="material-item download-material-item">
                            <div className="material-content">
                              <div className="material-info">
                                <h3>{material.title}</h3>
                                <p>{material.description}</p>
                                <div className="material-meta">
                                  <span className="file-type">{material.fileType.toUpperCase()}</span>
                                  <span className="file-size">{material.fileSize}</span>
                                  <span className="upload-date">Uploaded: {material.uploadDate}</span>
                                </div>
                              </div>
                              <DownloadButton
                                materialId={material.id}
                                fileName={material.title}
                                fileType={material.fileType as any}
                                fileSize={material.fileSize}
                                onDownload={handleDownload}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state">
                        <p>No learning materials available</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style>{css}</style>

      {showLogoutConfirm && (
        <ConfirmationModal
          isOpen={showLogoutConfirm}
          onClose={() => setShowLogoutConfirm(false)}
          onConfirm={() => {
            alert('Logging out...')
            setShowLogoutConfirm(false)
          }}
          title="Log Out"
          message="Are you sure you want to log out?"
          confirmText="Confirm"
          cancelText="Cancel"
        />
      )}
    </div>
  )
}

const css = `
:root{
  --sh-border:#EAEAEA;
  --sh-muted:#6D6D78;
  --sh-text:#172239;
  --sh-card-bg:#FFFFFF;
  --sh-shadow:0 8px 24px rgba(0,0,0,0.04);
  --sh-orange:#F6B48E;
  --sh-blue:#4A90E2;
}

/* Layout */
.course-detail-layout{
  display:grid;
  grid-template-columns:280px 1fr;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  min-height:100vh;
  height:100vh;
  overflow:hidden; /* 固定整体高度，外层不滚动 */
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  background: #fff;
}

.cd-main{
  background:#fff;
  border-radius:20px;
  padding:24px;
  box-shadow:0 4px 16px rgba(0,0,0,0.04);
  display:flex;
  flex-direction:column;
  min-height:100%;
  overflow:hidden; /* 右侧容器不滚动 */
}

/* Left sidebar — 与 StudentHome 一致 */
.sh-sidebar{display:flex;flex-direction:column;gap:24px}
.sh-profile-card{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-profile-card .avatar{width:48px;height:48px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:#F4F6FA;border:1px solid var(--sh-border)}
.sh-profile-card .info .name{font-size:14px;font-weight:700}
.sh-profile-card .info .email{font-size:12px;color:var(--sh-muted)}
.sh-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--sh-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center}
.sh-nav{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-nav .item{display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--sh-muted);text-decoration:none;font-weight:500}
.sh-nav .item.active{background:#FFA87A;color:#172239;font-weight:800;border-radius:20px}
.sh-nav .nav-icon{width:20px;height:20px}
.sh-ai-card{padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);display:flex;flex-direction:column;align-items:center;text-align:center;gap:28px;flex:1;min-height:280px}
.sh-ai-card .ai-title{font-weight:800;font-size:18px}
.sh-ai-card .ai-sub{color:var(--sh-muted);font-size:14px}
.sh-ai-card .ai-icon{width:56px;height:56px;border-radius:14px;background:var(--sh-blue);display:grid;place-items:center}
.btn-outline{padding:14px;border-radius:14px;background:#fff;border:1px solid var(--sh-border);font-weight:600;margin-top:auto}
/* Start Chat 按钮（与 StudentHome 一致） */
.btn-primary.ghost{
  margin-top:px;display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;cursor:pointer;font-weight:800;font-size:16px;
  width:100%; min-width:unset;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease;
}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}

/* Middle */
.cd-main{display:flex;flex-direction:column;gap:16px;min-height:100%;height:100%;overflow:hidden}
.cd-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.cd-title-section{display:flex;flex-direction:column;gap:12px;flex:1}
.back-btn{padding:8px 16px;border:1px solid var(--sh-border);border-radius:8px;background:#fff;cursor:pointer;font-size:14px;align-self:flex-start}
.cd-title{font-size:24px;font-weight:800;margin:0}
.cd-actions{display:flex;align-items:center;gap:10px}
.global-actions{position:fixed;top:32px;right:32px;z-index:10;display:flex;gap:12px}
.icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center}

/* 详情页右侧容器：一张卡片填满，外层不滚动，仅内部滚动 */
.sc-board{
  margin-top:0;
  border:none;
  border-radius:24px;
  background:transparent;
  box-shadow:none;
  display:flex;
  padding:0;
  flex:1;
  min-height:0;
  height:100%;
  overflow:hidden; /* 外层容器不滚动 */
}

.courses-grid{
  display:grid;
  grid-template-columns:1fr; /* 仅一张详情卡片 */
  gap:0;
  padding:0;
  width:100%;
  height:100%;
}

/* Header aligned with My Courses */
.sc-header{display:flex;align-items:center;gap:8px}
.sc-title{font-size:24px;font-weight:800}
.sc-search{display:flex;align-items:center;gap:8px;border:1.5px solid #E5E8F0;border-radius:20px;padding:10px 12px;background:#fff;min-width:360px}
.sc-search input{border:none;outline:none;flex:1;font-size:14px}
.sc-actions{display:flex;align-items:center;gap:10px;margin-left:auto}

/* Header section with transparent background */
/* Clean transparent hero */
.cd-hero-clean{
  position:relative;
  text-align:left;
  padding:4px 0 8px; /* 继续压缩上方留白 */
  margin-bottom:6px;
  background:transparent;
}
/* 横线置于头部底部，图片会部分跨过这条线 */
.cd-hero-clean::after{
  content:'';
  position:absolute;
  left:0; right:0; bottom:0;
  height:1px;
  background:#E6EAF2;      /* 略深一点，线更清晰 */
  z-index:2;               /* 横线在最上层，不被图片遮挡 */
  pointer-events:none;
}
.cd-hero-clean .back-circle{
  position:absolute;
  left:6px;
  top:6px; /* 更贴边 */
}
.course-meta-row{
  display:flex;
  align-items:flex-end;    /* 让图片与标题底部更靠近横线 */
  flex-wrap:wrap;
  gap:24px;
  margin-left:64px;        /* 右移避开返回按钮 */
  min-height:88px;
}
.cd-hero-clean .course-title-section{
  display:flex;
  flex-direction:column;
  gap:4px;
  align-items:flex-start;
  text-align:left;
}
.back-circle{
  width:40px;
  height:40px;
  border-radius:999px;
  border:1px solid var(--sh-border);
  background:#fff;
  display:grid;
  place-items:center;
  cursor:pointer;
  line-height:1;
  flex-shrink:0;
  margin-top:8px;
  box-shadow:0 2px 6px rgba(0,0,0,0.06);
  transition: all .2s ease;
}
.back-circle:hover{
  border-color:#E0E4EE;
  background:#f8fafc;
  box-shadow:0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}
.back-circle:active{
  transform: translateY(0);
}
.chev-left{
  transform: rotate(180deg);
  opacity:.8;
}
.back-circle:hover .chev-left{ opacity:1; }
.back-circle:focus{
  outline:3px solid #CFE4FF;
  outline-offset:2px;
}
.course-info{
  display:flex;
  align-items:center;
  gap:20px;
  flex:1;
}
/* Pure image — no badge/background, larger size and centered */
.course-illustration{
  width:auto;
  height:112px;            /* 提高视窗，确保上缘不被裁 */
  margin:0;
  background:transparent;
  border-radius:12px;      /* 轻微圆角，柔和 */
  overflow:hidden;         /* 只显示图片的一部分 */
  box-shadow:none;
  position:relative;
  z-index:1;               /* 线在上层（z-index:2） */
  padding-top:14px;        /* 为顶部插画留出空间，避免被裁 */
}
.course-illustration img{
  width:200px;             /* 放大插画，仅露出部分 */
  height:auto;
  object-fit:contain;
  display:block;
  transform: translateY(6px);  /* 微下移，顶部完整可见，底部轻微压线 */
  filter:none;
}
@media (max-width: 900px){
  .course-illustration{ height:96px; }
  .course-illustration img{ width:170px; transform: translateY(4px); }
}
.course-title-section{
  display:flex;
  flex-direction:column;
  gap:8px;
}
.course-title{
  font-size:28px;          /* 提升层级，减少“轻薄感” */
  font-weight:800;
  color:#172239;
  margin:0;
  letter-spacing:.2px;
}
.course-subtitle{
  font-size:16px;
  color:var(--sh-muted);
  margin:0;
  line-height:1.5;
  margin-bottom: 12px;
}

.course-overall-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.progress-label {
  font-size: 14px;
  color: var(--sh-muted);
  font-weight: 600;
  min-width: 120px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #F0F2F7;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4CAF50;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-percent {
  font-size: 14px;
  font-weight: 700;
  color: #172239;
  min-width: 40px;
  text-align: right;
}

/* Course detail card */
.course-detail-card{
  display:flex;
  flex-direction:column;
  gap:20px;
  padding:28px;
  height:100%;
  box-sizing:border-box;
  background:#fff;
  border-radius:20px;
  box-shadow:0 4px 20px rgba(0,0,0,0.06);
  overflow:hidden; /* 确保卡片内部内容不会溢出 */
}
.course-detail-content{
  display:flex;
  flex-direction:column;
  gap:28px;
  flex:1;
  min-height:0;
  overflow-y:auto; /* 确保垂直滚动 */
  overflow-x:hidden; /* 隐藏水平滚动 */
  padding-right:12px;
  max-height:calc(100vh - 200px); /* 设置最大高度确保滚动 */
}
.cd-description h2,.cd-section h2{
  font-size:22px;
  font-weight:700;
  margin-bottom:20px;
  color:#172239;
}
.cd-description p{
  color:var(--sh-muted);
  line-height:1.7;
  font-size:15px;
}
.cd-sections{
  display:flex;
  flex-direction:column;
  gap:36px;
}
.cd-section{
  border:none;
  border-radius:16px;
  padding:24px;
  background:#f8f9fa;
  border-left:4px solid var(--sh-orange);
}
.task-list,.material-list{
  display:flex;
  flex-direction:column;
  gap:20px;
}
.task-item,.material-item{
  border:none;
  border-radius:12px;
  padding:16px;
  background:#fff;
  box-shadow:0 2px 8px rgba(0,0,0,0.04);
  transition:transform 0.2s ease;
}
.task-item:hover,.material-item:hover{
  transform:translateY(-2px);
}
.task-info h3,.material-link h3{
  font-size:17px;
  font-weight:600;
  margin-bottom:8px;
  color:#172239;
}
.task-info p,.material-link p{
  color:var(--sh-muted);
  font-size:14px;
  margin-bottom:12px;
  line-height:1.5;
}
.task-meta{display:flex;gap:8px;margin:8px 0}
.meta-chip{font-size:12px;color:#6D6D78;background:#F8F8FA;border:1px solid #EFEFF2;padding:2px 8px;border-radius:999px;font-weight:700}
.deadline{
  color:#E53E3E;
  font-size:13px;
  font-weight:600;
  background:#FEE;
  padding:4px 8px;
  border-radius:6px;
  display:inline-block;
}
.material-link{
  text-decoration:none;
  color:inherit;
  display:block;
}
.material-link:hover{
  background:transparent;
}

/* 下载材料项样式 */
.download-material-item {
  padding: 20px !important;
}

.download-material-item .material-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  width: 100%;
}

.download-material-item .material-info {
  flex: 1;
}

.download-material-item .material-info h3 {
  margin-bottom: 8px;
  color: #172239;
  font-size: 16px;
  font-weight: 600;
}

.download-material-item .material-info p {
  margin-bottom: 12px;
  color: #6d6d78;
  font-size: 14px;
  line-height: 1.4;
}

.download-material-item .material-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #95a5a6;
}

.download-material-item .material-meta span {
  padding: 2px 6px;
  background: #f8f9fa;
  border-radius: 4px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .download-material-item .material-content {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .download-material-item .material-info {
    text-align: center;
  }
  
  .download-material-item .material-meta {
    justify-content: center;
  }
}
.empty-state{
  text-align:center;
  color:var(--sh-muted);
  padding:40px 0;
  font-size:16px;
}

.loading{display:grid;place-items:center;height:200px;font-size:18px;color:var(--sh-muted)}

/* Thin, light scrollbar only for the inner scroll area */
.course-detail-content{
  scrollbar-width: thin;                 /* Firefox */
  scrollbar-color: rgba(23,34,57,0.25) transparent; /* Firefox thumb/track */
  scrollbar-gutter: stable;              /* Keep layout stable when scrollbar appears */
}
/* WebKit browsers (Chrome, Edge, Safari) */
.course-detail-content::-webkit-scrollbar{
  width:8px;
}
.course-detail-content::-webkit-scrollbar-track{
  background: transparent;
}
.course-detail-content::-webkit-scrollbar-thumb{
  background: rgba(23,34,57,0.25);
  border-radius: 8px;
  border: 2px solid transparent; /* creates a thinner visual bar */
  background-clip: content-box;
}
.course-detail-content:hover::-webkit-scrollbar-thumb{
  background: rgba(23,34,57,0.35);
}
`