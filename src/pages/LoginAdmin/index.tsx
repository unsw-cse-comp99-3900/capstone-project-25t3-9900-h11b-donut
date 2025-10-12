import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import illustration from '../../assets/images/illustration-admin.png'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'

export function LoginAdmin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <div className="signup-container theme-admin">
      {/* 左侧插画面板（Admin 专属插图） */}
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
          <button className="back-btn" aria-label="Back" onClick={() => history.back()}>
            <img src={ArrowRight} width={16} height={16} alt="" style={{ transform: 'scaleX(-1)' }} />
          </button>
          <Header title="Login Now" subtitle="Admin" />
        </div>

        <div className="role-section-inner" style={{ marginTop: 96 }}>
          <div className="card login-card">
            <div className="form-row">
              <TextInput
                label="Email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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

            <div className="form-row" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <a className="link" href="#" onClick={(e) => e.preventDefault()}>Forgot password?</a>
            </div>

            <div className="form-row btn-stack">
              <button className="ghost-btn" onClick={() => { window.location.hash = '/signup-admin' }}>
                <span>Sign Up</span>
                <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
              </button>
              <button className="ghost-btn" style={{ marginTop: 16 }}>
                <span>Login</span>
                <img className="arrow" src={ArrowRight} width={16} height={16} alt="" aria-hidden />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}