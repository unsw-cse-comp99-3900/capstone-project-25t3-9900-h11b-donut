import { useState, useMemo, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import IconSearch from '../../assets/icons/search-24.svg'
import IconHelp from '../../assets/icons/help-24.svg'
import IconBell from '../../assets/icons/bell-24.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import UserWhite from '../../assets/icons/user-24-white.svg'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import { coursesStore } from '../../store/coursesStore'
import illoOrange from '../../assets/images/illustration-orange.png'
import illoStudent from '../../assets/images/illustration-student.png'
import illoAdmin from '../../assets/images/illustration-admin.png'

const illoMap: Record<'orange' | 'student' | 'admin', string> = {
  orange: illoOrange,
  student: illoStudent,
  admin: illoAdmin,
}
export function StudentCourses() {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [q, setQ] = useState('')
  const [v, setV] = useState(0)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalConfig, setModalConfig] = useState<{
    action: 'add' | 'remove'
    courseId: string
    courseTitle: string
  } | null>(null)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  useEffect(() => {
    const unsub = coursesStore.subscribe(() => setV(s => s + 1))
    return unsub
  }, [])
  const matches = useMemo(() => {
    const t = q.trim().toLowerCase()
    if (!t) return []
    
    const filtered = coursesStore.availableCourses.filter(course => 
      course.id.toLowerCase().startsWith(t) || 
      course.title.toLowerCase().startsWith(t) ||
      course.desc.toLowerCase().startsWith(t)
    )
    // Courses already in "My Courses" are displayed first
    const mySet = new Set(coursesStore.myCourses.map(c => c.id))
    const sorted = filtered.sort((a, b) => {
      const inMyA = mySet.has(a.id) ? 1 : 0
      const inMyB = mySet.has(b.id) ? 1 : 0
      return inMyB - inMyA
    })
    return sorted
  }, [q, v])
  return (
    <div className="student-courses-layout">
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
          <a className="item active" href="#/student-courses">
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

      {/* Middle: 课程列表页 */}
      <main className="sc-main">
        <header className="sc-header">
          <h1 className="sc-title">Courses 📖</h1>
          <div className="sc-search">
            <img src={IconSearch} width={16} height={16} alt="" />
            <input type="text" placeholder="Search" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div className="sc-actions global-actions">
            <button className="icon-btn" aria-label="Help"><img src={IconHelp} width={20} height={20} alt="" /></button>
            <button className="icon-btn" aria-label="Notifications"><img src={IconBell} width={20} height={20} alt="" /></button>
          </div>
        </header>

        <section className={`sc-board ${matches.length > 0 ? '' : (q.trim() ? '' : (coursesStore.myCourses.length > 0 ? '' : 'empty'))}`}>
          {matches.length > 0 ? (
            <div className="course-result">
              {matches.map(match => {
                const inMy = coursesStore.myCourses.some(c => c.id === match.id)
                return (
                  <div key={match.id} className="big-card">
                    <div className="thumb"><img src={illoMap[match.illustration]} alt="" /></div>
                    <div className="info">
                      <div className="cr-title">{match.id}</div>
                      <div className="cr-desc">{match.desc}</div>
                    </div>
                    <div className="add-btn-container">
                      <button
                        className={`add-btn ${inMy ? 'danger' : ''}`}
                        onClick={() => {
                          if (inMy) {
                            setModalConfig({
                              action: 'remove',
                              courseId: match.id,
                              courseTitle: match.id
                            })
                            setModalOpen(true)
                          } else {
                            setModalConfig({
                              action: 'add',
                              courseId: match.id,
                              courseTitle: match.id
                            })
                            setModalOpen(true)
                          }
                        }}
                      >
                        {inMy ? 'Remove' : 'Add to My Courses'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : q.trim() ? (
            <div className="empty">No courses found for "{q}"</div>
          ) : coursesStore.myCourses.length > 0 ? (
            <div className="my-courses-list">
              <div className="courses-grid">
                {coursesStore.myCourses.map(course => (
                  <div 
                    key={course.id} 
                    className="course-card"
                    onClick={() => window.location.hash = `#/course-detail/${course.id}`}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="course-thumb"><img src={illoMap[course.illustration]} alt="" /></div>
                    <div className="course-info">
                      <div className="course-title">{course.id}</div>
                      <div className="course-desc">{course.desc}</div>
                    </div>
                    <button
                      className="remove-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setModalConfig({
                          action: 'remove',
                          courseId: course.id,
                          courseTitle: course.id
                        })
                        setModalOpen(true)
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="sp-placeholder">
              <div className="sp-empty-title">No courses found yet.</div>
              <div className="sp-empty-sub">Search a course name or code and add it to your own course!</div>
            </div>
          )}
        </section>
      </main>

      <style>{css}</style>

      {modalConfig && (
        <ConfirmationModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConfirm={() => {
            if (modalConfig.action === 'add') {
              coursesStore.addCourse(modalConfig.courseId)
              setQ('')
              window.location.hash = '#/student-courses'
            } else {
              coursesStore.removeCourse(modalConfig.courseId)
            }
            setModalOpen(false)
            setModalConfig(null)
          }}
          title={modalConfig.action === 'add' ? 'Add Course' : 'Remove Course'}
          message={
            modalConfig.action === 'add'
              ? `Are you sure you want to add "${modalConfig.courseTitle}" to your courses?`
              : `Are you sure you want to remove "${modalConfig.courseTitle}" from your courses?`
          }
          confirmText={modalConfig.action === 'add' ? 'Confirm' : 'Confirm'}
          cancelText="Cancel"
        />
      )}

      {showLogoutConfirm && (
        <ConfirmationModal
          isOpen={showLogoutConfirm}
          onClose={() => setShowLogoutConfirm(false)}
          onConfirm={() => {
            setShowLogoutConfirm(false)
            window.location.hash = '#/login-student'
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
.student-courses-layout{
  display:grid;
  grid-template-columns:280px 1fr;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  min-height:100vh;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
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
/* Start Chat 按钮（与 Generate 按钮一致） */
.btn-primary.ghost{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;font-weight:800;font-size:16px;width:100%;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}

/* Middle */
.sc-main{display:flex;flex-direction:column;gap:16px;min-height:calc(100vh - 64px)}
.sc-header{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.sc-title{font-size:24px;font-weight:800;margin:0}
.sc-search{display:flex;align-items:center;gap:8px;border:1.5px solid #E5E8F0;border-radius:20px;padding:10px 12px;background:#fff;min-width:360px}
.sc-search input{border:none;outline:none;flex:1;font-size:14px}
.sc-actions{display:flex;align-items:center;gap:10px;margin-left:auto}
.icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center}
.global-actions{position:fixed;top:32px;right:32px;z-index:10;display:flex;gap:12px}
.sc-board{margin-top:12px;border:none;border-radius:0;background:transparent;box-shadow:none;min-height:0;display:flex;flex-direction:column;padding:0;height:100%;overflow:hidden}
.sc-board.empty{
  margin-top:14px;
  border:none;
  border-radius:0;
  background:transparent;
  box-shadow:none;
  min-height:520px;
  display:grid;
  place-items:center;
  padding:0;
  height:auto; /* 覆盖 .sc-board 的 height:100%，与 StudentPlan 一致 */
}
/* 让 Courses 的主区域高度与 StudentPlan 一致，避免空态居中位置下移 */
.sc-main{min-height:auto}
.sp-placeholder{text-align:center;max-width:600px}
.sp-empty-title{font-weight:800;font-size:20px;color:#172239;margin-bottom:8px}
.sp-empty-sub{font-size:16px;color:#6D6D78}
.course-result{width:100%;padding:16px;display:grid;grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));gap:20px;justify-content:flex-start;max-height:calc(100vh - 200px);overflow-y:auto;scrollbar-width:thin;scrollbar-color:#E5E8F0 transparent}
.course-result::-webkit-scrollbar{width:8px}
.course-result::-webkit-scrollbar-track{background:transparent}
.course-result::-webkit-scrollbar-thumb{background:rgba(23,34,57,0.25);border-radius:8px;border:2px solid transparent;background-clip:content-box}
.course-result:hover::-webkit-scrollbar-thumb{background:rgba(23,34,57,0.35)}
.courses-grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));gap:22px;padding:18px;width:100%;max-height:calc(100vh - 200px);overflow-y:auto;scrollbar-width:thin;scrollbar-color:#E5E8F0 transparent}
.courses-grid::-webkit-scrollbar{width:8px}
.courses-grid::-webkit-scrollbar-track{background:transparent}
.courses-grid::-webkit-scrollbar-thumb{background:rgba(23,34,57,0.25);border-radius:8px;border:2px solid transparent;background-clip:content-box}
.courses-grid:hover::-webkit-scrollbar-thumb{background:rgba(23,34,57,0.35)}
.course-card{background:#fff;border-radius:20px;padding:20px;cursor:pointer;transition:all 0.3s ease;box-shadow:0 2px 8px rgba(0,0,0,0.08);display:flex;flex-direction:column;gap:12px;position:relative}
.course-card:hover{box-shadow:0 8px 24px rgba(0,0,0,0.12);transform:translateY(-4px)}
.course-thumb{width:100%;height:130px;border-radius:10px;overflow:hidden;background:#F6B48E;display:grid;place-items:center}
.course-thumb img{width:100%;height:100%;object-fit:cover}
.course-info{flex:1;display:flex;flex-direction:column;gap:8px}
.course-title{font-size:18px;font-weight:700;color:#172239;font-family:'Montserrat',sans-serif;line-height:1.3}
.course-desc{color:#666;font-size:14px;line-height:1.5;flex:1}
.remove-btn{padding:10px 16px;border-radius:10px;background:#FF6B6B;border:none;color:#fff;font-weight:600;cursor:pointer;position:absolute;bottom:16px;right:16px;transition:all 0.2s ease;font-size:13px}
.remove-btn:hover{background:#FF5252;transform:scale(1.05)}
.big-card{display:flex;flex-direction:column;width:100%;height:300px;border:1px solid var(--sh-border);border-radius:24px;background:#fff;box-shadow:var(--sh-shadow);padding:0;overflow:hidden;cursor:pointer;transition:all 0.3s ease}
.big-card:hover{transform:translateY(-4px);box-shadow:0 12px 32px rgba(0,0,0,0.12)}
.big-card .thumb{width:100%;height:140px;background:#F6B48E;display:grid;place-items:center;overflow:hidden;position:relative}
.big-card .thumb img{width:120%;height:auto}
.big-card .info{padding:20px;flex:1;display:flex;flex-direction:column;gap:12px}
.big-card .info .cr-title{font-size:19px;font-weight:800;line-height:1.2}
.big-card .info .cr-desc{font-size:13px;color:var(--sh-muted);line-height:1.4;flex:1}
.big-card .add-btn-container{padding:0 20px 20px 20px}
.add-btn{width:100%;padding:14px;border-radius:16px;background:#F6B48E;border:none;color:#172239;font-weight:800;cursor:pointer;font-size:13px;transition:all 0.2s ease}
.add-btn:hover{background:#FFA87A;transform:scale(1.02)}
/* 搜索结果中：当课程已在我的课程里，显示红色 Remove 按钮以与 Add 区分 */
.add-btn.danger{background:#FF6B6B;color:#fff}
.add-btn.danger:hover{background:#FF5252;transform:scale(1.02)}
`