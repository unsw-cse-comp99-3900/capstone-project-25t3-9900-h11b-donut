import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import { PrimaryButton } from '../../components/PrimaryButton'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import illustration from '../../assets/images/illustration-student.png'

export function SignupStudent() {
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')

  return (
    <div className="signup-container theme-student">
      {/* Left illustration area: Reuse student illustration and text */}
      <section className="illustration-panel">
        <div className="illustration-bg" />
        <img className="illustration-image" src={illustration} alt="" />
        <div className="illustration-text" style={{ top: 590 }}>
          <h2 className="h2 title">Fully Flexible Schedule</h2>
          <p className="p2 body">There is no set schedule and you can learn whenever you want to.</p>
        </div>
      </section>

      {/* Right registration form */}
      <section className="role-section">
        <div className="header">
          <button className="back-btn" aria-label="Back" onClick={() => history.back()}>
            <img src={ArrowRight} width={16} height={16} alt="" style={{ transform: 'scaleX(-1)' }} />
          </button>
          <Header title="Sign Up Now" subtitle="Student" />
        </div>

        <div className="role-section-inner" style={{ marginTop: 32 }}>
          <div className="card login-card">
            {/* Avatar upload placeholder (optional) */}
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 16 }}>
              <div className="avatar-uploader">
                <span className="p3" style={{ textAlign: 'center' }}>
                  Upload Profile<br />Picture<br />(Optional)
                </span>
              </div>
            </div>

            <div className="form-row">
              <TextInput
                label="Email Address"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <TextInput
                label="Full Name"
                placeholder="Your full name"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <TextInput
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-row" style={{ marginTop: 32 }}>
              <PrimaryButton
                text="Create Account"
                onClick={() => { window.location.hash = '/login-student' }}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}