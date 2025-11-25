import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import illustration from '../../assets/images/illustration-admin.png'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import apiService from '../../services/api'
import { courseAdmin } from '../../store/coursesAdmin'

export function LoginAdmin() {
  const [adminId, setID] = useState('')
  const [error, setError] = useState('')     
  const [loading, setLoading] = useState(false)
  const [password, setPassword] = useState('')
  const handleLogin = async () => {           
      setError('')
      if (!adminId || !password) {
        setError('PLEASE ENTER YOUR ID OR PASSWORD!')
        return
      }
      try {
        setLoading(true)
        await apiService.login_adm(adminId, password)
        await courseAdmin.getMyCourses(true)
        await courseAdmin.getMyTasks(true)
        await courseAdmin.getMyMaterials(true)
        await courseAdmin.getMyQuestions(true)
        window.location.hash = '/admin-home'
      } catch (e: any) {
        setError(e?.message || 'FAIL TO SIGNIN')
      } finally {
        setLoading(false)
      }
    }
  return (
    <div className="signup-container theme-admin">
      {/* Left illustration panel (Admin exclusive illustration) */}
      <section className="illustration-panel">
        <div className="illustration-bg" />
        <img className="illustration-image" src={illustration} alt="" />
        <div className="illustration-text" style={{ top: 590 }}>
          <h2 className="h2 title">Connect with the Students</h2>
          <p className="p2 body">You can easily connect with thousands of students by using out platform.</p>
        </div>
      </section>

      <section className="role-section">
        <div className="header">
          <button className="back-btn" aria-label="Back" onClick={() => window.location.hash = '#/login'}>
            <img src={ArrowRight} width={16} height={16} alt="" style={{ transform: 'scaleX(-1)' }} />
          </button>
          <Header title="Login Now" subtitle="Admin" />
        </div>

        <div className="role-section-inner" style={{ marginTop: 96 }}>
          <div className="card login-card">
            <div className="form-row">
              <TextInput
                label="Admin_ID"
                type="id"
                placeholder="z123456"
                value={adminId}
                onChange={(e) => setID(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <TextInput
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="form-row">
                <p style={{ color: 'red', margin: 0 }}>{error}</p>
              </div>
            )}
            <div className="form-row" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <a className="link" href="#" onClick={(e) => e.preventDefault()}>Forgot password?</a>
            </div>

            <div className="form-row btn-stack">
              <button className="ghost-btn" onClick={() => { window.location.hash = '/signup-admin' }}>
                <span>Sign Up</span>
                <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
              </button>
              <button className="ghost-btn"  style={{ marginTop: 16, opacity: loading ? 0.7 : 1 }}
                onClick={handleLogin}
                disabled={loading}>
                <span>{loading ? 'Logging in...' : 'Login'}</span>
                <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}