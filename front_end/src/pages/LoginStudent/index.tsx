import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import illustration from '../../assets/images/illustration-student.png'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import apiService from '../../services/api'

export function LoginStudent() {
  //const [email,] = useState('')
  const [password, setPassword] = useState('')
  const [studentId, setID] = useState('')
  const [error, setError] = useState('')     //  补上错误状态
  const [loading, setLoading] = useState(false) // 可选：加载中状态

  const handleLogin = async () => {           //  绑定到按钮
    setError('')
    if (!studentId || !password) {
      setError('PLEASE ENTER YOUR ID OR PASSWORD!')
      return
    }
    try {
      setLoading(true)
      await apiService.login(studentId, password)
      window.location.hash = '/student-home'
    } catch (e: any) {
      setError(e?.message || 'FAIL TO SIGNIN')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="signup-container theme-student">
      {/* 左侧插画 */}
      <section className="illustration-panel">
        <div className="illustration-bg" />
        <img className="illustration-image" src={illustration} alt="" />
        <div className="illustration-text" style={{ top: 590 }}>
          <h2 className="h2 title">Fully Flexible Schedule</h2>
          <p className="p2 body">There is no set schedule and you can learn whenever you want to.</p>
        </div>
      </section>

      <section className="role-section">
        <div className="header">
          <button className="back-btn" aria-label="Back" onClick={() =>window.location.hash = '#/signup'}> 
            <img src={ArrowRight} width={16} height={16} alt="" style={{ transform: 'scaleX(-1)' }} />
          </button>
          <Header title="Login Now" subtitle="Student" />
        </div>

        <div className="role-section-inner" style={{ marginTop: 96 }}>
          <div className="card login-card">
            <div className="form-row">
              <TextInput
                label="Student_ID"
                type="id"
                placeholder="z123456"
                value={studentId}
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

            {/* 错误提示 */}
            {error && (
              <div className="form-row">
                <p style={{ color: 'red', margin: 0 }}>{error}</p>
              </div>
            )}

            <div className="form-row" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <a className="link" href="#" onClick={(e) => e.preventDefault()}>Forgot password?</a>
            </div>

            <div className="form-row btn-stack">
              <button className="ghost-btn" onClick={() => { window.location.hash = '/signup-student' }}>
                <span>Sign Up</span>
                <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
              </button>

              {/* ✅ 登录按钮调用 handleLogin，而不是直接跳转 */}
              <button
                className="ghost-btn"
                style={{ marginTop: 16, opacity: loading ? 0.7 : 1 }}
                onClick={handleLogin}
                disabled={loading}
              >
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
