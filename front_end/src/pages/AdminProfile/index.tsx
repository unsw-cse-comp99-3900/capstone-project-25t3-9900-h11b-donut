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

// 图片映射 - 循环使用4张图片
const adminIllustrations = [
  illustrationAdmin,
  illustrationAdmin2, 
  illustrationAdmin3,
  illustrationAdmin4
];

export function AdminProfile() {
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const uid = localStorage.getItem('current_user_id') || '';
  const [user, setUser] = useState<{ name?: string; email?: string; avatarUrl?: string } | null>(() => {
    if (!uid) return null;
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'); }
    catch { return null; }
  });

  // 修改密码状态
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')

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
  }, [uid]);

  const handleLogout = () => {
    setLogoutModalOpen(true);
  };

  const confirmLogout = async () => {
    try { await apiService.logout_adm(); }
    finally {
      window.location.hash = '#/login-admin';
      setLogoutModalOpen(false);
    }
  };

  const handleChangePassword = () => {
    setPasswordModalOpen(true);
    setNewPassword('');
    setConfirmPassword('');
    setPasswordError('');
  };

  const confirmChangePassword = async () => {
    if (newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters long');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    try {
      // 这里调用修改密码的API
      // await apiService.changePassword(newPassword);
      alert('Password changed successfully!');
      setPasswordModalOpen(false);
      setNewPassword('');
      setConfirmPassword('');
      setPasswordError('');
    } catch (error) {
      setPasswordError('Failed to change password');
    }
  };

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const newAvatarUrl = e.target?.result as string;
        // 更新用户头像
        if (uid) {
          const userData = JSON.parse(localStorage.getItem(`u:${uid}:user`) || '{}');
          userData.avatarUrl = newAvatarUrl;
          localStorage.setItem(`u:${uid}:user`, JSON.stringify(userData));
          setUser(userData);
        }
      };
      reader.readAsDataURL(file);
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
          <button className="chevron" aria-label="Open profile" onClick={() => (window.location.hash = '#/admin-home')}>
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
            <div className="hello">Profile Settings</div>
            <h1 className="title">Manage Your Account <span className="wave" aria-hidden>👤</span></h1>
          </div>
        </header>

        {/* 个人信息区域 */}
        <section className="profile-section">
          <div className="profile-header">
            <div className="avatar-section">
              <div className="avatar-container">
                <img
                  src={user?.avatarUrl || AvatarIcon}
                  width={176}
                  height={176}
                  alt="avatar"
                  className="profile-avatar"
                  onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
                />
                <label className="avatar-upload-btn" htmlFor="avatar-upload">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 16L12 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M8 12L16 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  Change Photo
                </label>
                <input
                  id="avatar-upload"
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={handleAvatarChange}
                />
              </div>
            </div>
            
            <div className="profile-info">
              <h2 className="profile-name">{user?.name || 'John Smith'}</h2>
              <p className="profile-email">{user?.email || 'johnsmith@gmail.com'}</p>
            </div>
          </div>
        </section>

        {/* 设置区域 */}
        <section className="settings-section">
          <h3 className="settings-title">Setting⚙️</h3>
          
          <div className="settings-grid">
            <div className="setting-card" onClick={handleChangePassword}>
              <div className="setting-icon">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect width="32" height="32" rx="9999" fill="#FC77A0"/>
                  <path d="M16 12V20M12 16H20" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
              <div className="setting-content">
                <h4 className="setting-title">Change Password</h4>
                <p className="setting-description">Reset your Password here.</p>
              </div>
            </div>


          </div>
        </section>


      </main>

      {/* 登出确认模态框 */}
      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={confirmLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Log Out"
        cancelText="Cancel"
      />

      {/* 修改密码模态框 */}
      <ConfirmationModal
        isOpen={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
        onConfirm={confirmChangePassword}
        title="Change Password"
        message={
          <div className="password-modal-content">
            <div className="password-input-group">
              <label>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                className="password-input"
              />
            </div>
            <div className="password-input-group">
              <label>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="password-input"
              />
            </div>
            {passwordError && <div className="password-error">{passwordError}</div>}
          </div>
        }
        confirmText="Change Password"
        cancelText="Cancel"
      />

      <style jsx>{`
        /* 侧栏与布局：与 AdminHome 保持完全一致 */
        :root{
          --ah-border:#EAEAEA;
          --ah-muted:#6D6D78;
          --ah-text:#172239;
          --ah-card-bg:#FFFFFF;
          --ah-shadow:0 8px 24px rgba(0,0,0,0.04);
          --ah-primary:#BB87AC;
          --ah-primary-light:rgba(187,135,172,0.49);
        }

        .admin-home-layout{
          display:grid;
          grid-template-columns:280px 1fr;
          gap:48px;
          padding:32px;
          color:var(--ah-text);
          background:#fff;
          min-height:100vh;
          font-family:'Montserrat',system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
        }

        .ah-sidebar{
          display:flex;flex-direction:column;gap:24px;height:100%;
        }

        .ah-profile-card{
          display:flex;align-items:center;gap:12px;
          padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
          height:95.36px;
        }
        .ah-profile-card .avatar{
          width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--ah-border);
        }
        .ah-profile-card .info .name{font-size:16px;font-weight:600}
        .ah-profile-card .info .email{color:var(--ah-muted);font-size:12px}
        .ah-profile-card .chevron{
          margin-left:auto;background:#fff;border:1px solid var(--ah-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center
        }

        .ah-nav{
          display:flex;flex-direction:column;gap:12px;
          padding:16px;border:1px solid var(--ah-border);border-radius:20px;background:#fff;box-shadow:var(--ah-shadow);
        }
        .ah-nav .item{
          display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--ah-muted);text-decoration:none;font-weight:500;
        }
        .ah-nav .item:hover{background:var(--ah-primary-light);color:var(--ah-text);}
        .ah-nav .item.active{background:var(--ah-primary);color:#172239;font-weight:600;border-radius:20px}
        .ah-nav .nav-icon{width:20px;height:20px}

        .ah-illustration{
          margin-top:auto;margin-bottom:20px;min-height:200px;display:flex;align-items:center;justify-content:center;
        }

        .btn-outline{
          padding:14px;border-radius:14px;background:#fff;border:1px solid var(--ah-border);cursor:pointer;font-weight:600;margin-top:auto;
        }

        /* 响应式（与 Home 相同） */
        @media (max-width:1200px){.admin-home-layout{grid-template-columns:240px 1fr}}
        @media (max-width:768px){.admin-home-layout{grid-template-columns:1fr;gap:16px;padding:16px}.ah-sidebar{order:2}.ah-main{order:1}}

        .ah-main {
          flex: 1;
          padding: 32px;
          overflow-y: auto;
        }

        .ah-header {
          margin-bottom: 32px;
        }

        .ah-header .hello {
          color: #6D6D78;
          font-size: 16px;
          margin-bottom: 4px;
        }

        .ah-header .title {
          color: #172239;
          font-size: 32px;
          font-weight: 600;
          margin: 0;
        }

        .profile-section {
          background: white;
          border-radius: 32px;
          padding: 32px;
          margin-bottom: 32px;
          border: 1px solid #EAEAEA;
        }

        .profile-header {
          display: flex;
          align-items: center;
          gap: 32px;
        }

        .avatar-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .avatar-container {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .profile-avatar {
          border-radius: 50%;
          object-fit: cover;
        }

        .avatar-upload-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: #BB87AC;
          color: white;
          border: none;
          border-radius: 20px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s;
        }

        .avatar-upload-btn:hover {
          filter: brightness(0.95);
        }

        .profile-info {
          text-align: center;
        }

        .profile-name {
          color: #172239;
          font-size: 24px;
          font-weight: 600;
          margin: 0 0 8px 0;
        }

        .profile-email {
          color: #6D6D78;
          font-size: 16px;
          margin: 0;
        }

        .settings-section {
          background: white;
          border-radius: 32px;
          padding: 32px;
          margin-bottom: 32px;
          border: 1px solid #EAEAEA;
        }

        .settings-title {
          color: #172239;
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 24px;
        }

        .settings-grid {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .setting-card {
          display: flex;
          align-items: center;
          gap: 24px;
          padding: 24px;
          border-radius: 32px;
          border: 1px solid #EAEAEA;
          cursor: pointer;
          transition: all 0.2s;
        }

        .setting-card:hover {
          background: #F8FAFC;
          transform: translateY(-2px);
        }

        .setting-icon {
          flex-shrink: 0;
        }

        .setting-content {
          flex: 1;
        }

        .setting-title {
          color: #172239;
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 8px 0;
        }

        .setting-description {
          color: #6D6D78;
          font-size: 14px;
          margin: 0;
        }

        .habit-section {
          background: white;
          border-radius: 32px;
          padding: 24px;
          border: 1px solid #EAEAEA;
        }

        .habit-card {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .habit-icon {
          flex-shrink: 0;
        }

        .habit-content {
          flex: 1;
        }

        .habit-title {
          color: #172239;
          font-size: 20px;
          font-weight: 600;
          margin: 0 0 8px 0;
        }

        .habit-description {
          color: #6D6D78;
          font-size: 14px;
          margin: 0 0 16px 0;
        }

        .progress-bar {
          position: relative;
          width: 198px;
          height: 8px;
          background: rgba(234, 234, 234, 0.48);
          border-radius: 5px;
          margin-bottom: 8px;
        }

        .progress-fill {
          position: absolute;
          height: 6px;
          background: #FFCB57;
          border-radius: 5px;
          top: 1px;
          left: 1px;
        }

        .progress-text {
          text-align: right;
          color: #172239;
          font-size: 12px;
          font-weight: 500;
          width: 198px;
        }

        .password-modal-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .password-input-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .password-input-group label {
          color: #172239;
          font-weight: 500;
          font-size: 14px;
        }

        .password-input {
          padding: 12px 16px;
          border: 2px solid #BB87AC;
          border-radius: 20px;
          font-size: 20px;
          font-weight: 600;
          color: #172239;
        }

        .password-input::placeholder {
          color: #6D6D78;
        }

        .password-error {
          color: #DC2626;
          font-size: 14px;
          text-align: center;
        }
      `}</style>
    </div>
  );
}