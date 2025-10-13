import { useState } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import UserWhite from '../../assets/icons/user-24-white.svg'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'

export function StudentProfile() {
  const [showForm, setShowForm] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  return (
    <div className="student-profile-layout">
      {/* 左侧沿用 StudentHome 侧栏 */}
      <aside className="sh-sidebar">
        <div
          className="sh-profile-card"
          onClick={() => (window.location.hash = '#/student-profile')}
          role="button"
          aria-label="Open profile"
          style={{ cursor: 'pointer' }}
        >
          <div className="avatar"><img src={AvatarIcon} width={48} height={48} alt="" /></div>
          <div className="info">
            <div className="name">John Smith</div>
            <div className="email">johnsmith@gmail.com</div>
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

      {/* 中间 Profile 信息 */}
      <main className="sp-main">
        <header className="sp-header">
          <h1 className="sp-title">Profile ✨</h1>
        </header>

        <section className="sp-center">
          <div className="sp-avatar-wrap">
            <div className="ring"></div>
            <div className="avatar-circle">
              <img src={AvatarIcon} width={96} height={96} alt="" />
            </div>
            <span className="badge">Student</span>
          </div>
          <button className="sp-edit-btn" type="button" aria-label="Edit profile">Edit</button>

          <div className="sp-name">John Smith</div>
          <div className="sp-email">johnsmith@gmail.com</div>
          <div className="sp-bonus">My bonus : 3.65</div>

          <section className="sp-settings">
            <h2 className="sp-subtitle">Setting</h2>
            <div className="sp-card" onClick={() => setShowForm(true)} role="button" aria-label="Change Password" style={{cursor:'pointer'}}>
              <div className="sp-card-icon">⭐</div>
              <div className="sp-card-body">
                <div className="sp-card-title">Change Password</div>
                <div className="sp-card-desc">Reset your Password here.</div>
              </div>
            </div>
          </section>
        </section>
      </main>

      {/* 右侧修改密码（点击 Setting 卡片后显示） */}
      {showForm && (
      <aside className="sp-right">
        <div className="sp-back">
          <button className="icon-btn" aria-label="Back" onClick={() => setShowForm(false)}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 14L5 8L11 2" stroke="#161616" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <div className="sp-form">
          <h3 className="sp-form-title">Change Password</h3>
          <label className="sp-field">
            <span>Old Password</span>
            <div className="input">
              <span className="lock">🔒</span>
              <input type="password" placeholder="xxxxx" />
            </div>
          </label>
          <label className="sp-field">
            <span>New Password</span>
            <div className="input">
              <span className="lock">🔒</span>
              <input type="password" placeholder="xxxxx" />
            </div>
          </label>
          <button className="btn-primary ghost ai-start sp-submit" onClick={() => alert('Submitted!')}>
            <span className="spc"></span>
            <span className="label">Submit</span>
            <img src={ArrowRight} width={16} height={16} alt="" className="chev" />
          </button>
        </div>
      </aside>
      )}

      <style>{css}</style>

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

.student-profile-layout{
  display:grid;
  grid-template-columns:280px 1fr 360px;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  min-height:100vh;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}

/* 侧栏（与 StudentHome 一致的关键样式子集） */
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
/* Start Chat 按钮与 Generate 按钮完全一致 */
.btn-primary.ghost{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;font-weight:800;font-size:16px;width:100%;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-primary.ghost .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}

/* 中间区域 */
.sp-main{display:flex;flex-direction:column;gap:24px}
.sp-header{display:flex;justify-content:flex-start}
.sp-header .sp-title{font-size:32px;font-weight:800}
.sp-center{display:flex;flex-direction:column;align-items:center;gap:12px;margin-top:8px}
.sp-avatar-wrap{position:relative;display:grid;place-items:center;margin:12px 0 6px}
.sp-avatar-wrap .ring{position:absolute;inset:-6px;border-radius:999px;border:6px solid transparent;border-top-color:#F08AA4;border-right-color:#F08AA4}
.sp-avatar-wrap .avatar-circle{width:120px;height:120px;border-radius:999px;overflow:hidden;display:grid;place-items:center;background:#F4F6FA;border:4px solid #fff;box-shadow:var(--sh-shadow)}
.sp-avatar-wrap .badge{position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);background:#FFA87A;color:#172239;border-radius:999px;padding:6px 10px;font-weight:700}
.sp-name{font-size:20px;font-weight:800}
.sp-email{font-size:14px;color:var(--sh-muted)}
.sp-bonus{font-size:14px;font-weight:700;margin-top:6px}
.sp-edit-btn{margin-top:10px;padding:8px 12px;border:1px solid var(--sh-border);border-radius:12px;background:#fff;font-weight:700;color:var(--sh-text);cursor:pointer;box-shadow:var(--sh-shadow)}
.sp-edit-btn:hover{background:#fafafa}
.sp-settings{width:100%;max-width:520px;margin-top:18px;margin-inline:auto}
.sp-subtitle{font-size:18px;font-weight:800;margin:8px 0 12px}
.sp-card{display:flex;align-items:center;gap:12px;padding:16px 18px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sp-card-icon{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;background:#FFF3EB}
.sp-card-title{font-weight:700}
.sp-card-desc{font-size:12px;color:var(--sh-muted)}

/* 右侧表单（简洁头部，仅返回） */
.sp-right{padding-top:8px;display:flex;flex-direction:column;gap:16px}
.sp-back{display:flex;align-items:center;justify-content:flex-start}
.icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center}
.sp-form{margin-top:8px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);padding:20px}
.sp-form-title{font-size:18px;font-weight:800;margin-bottom:12px}
.sp-field{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}
.sp-field > span{font-size:12px;color:var(--sh-muted)}
.sp-field .input{display:flex;align-items:center;gap:8px;border:2px solid #C9D8F3;border-radius:14px;padding:10px 12px}
.sp-field .input input{border:none;outline:none;flex:1;font-size:14px}
.sp-submit{margin-top:8px}
@media (max-width: 1200px){
  .student-profile-layout{grid-template-columns:240px 1fr}
}
`