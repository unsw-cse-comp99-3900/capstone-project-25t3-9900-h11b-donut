import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import { PrimaryButton } from '../../components/PrimaryButton'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import illustration from '../../assets/images/illustration-student.png'
import apiService from '../../services/api'
import AvatarPicker from "../../components/AvatarPicker"; 
export function SignupStudent() {
  const [email, setEmail] = useState('')
  const [studentId, setStudentId] = useState('') 
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>('')       // 错误消息
  const [loading, setLoading] = useState<boolean>(false) // 加载状态
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const handleRegister = async (): Promise<void> => {
    setError('')
    if (!email || !password) {
      setError('请输入邮箱和密码')
      return
    }

    try {
      setLoading(true)
      await apiService.register(studentId,email, password,avatarFile || undefined)
      alert('注册成功！')
      window.location.hash = '/login-student'
    } catch (e: any) {
      setError(e?.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

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
              <AvatarPicker value={avatarFile} onChange={setAvatarFile} />
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
                label="Student ID (zid)"
                placeholder="z1234567"
                 value={studentId}
                onChange={e => setStudentId(e.target.value)}
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

            {/* ✅ 错误信息显示 */}
            {error && (
              <div className="form-row">
                <p style={{ color: 'red', margin: 0 }}>{error}</p>
              </div>
            )}

            <div className="form-row" style={{ marginTop: 32 }}>
              <PrimaryButton
                text={loading ? 'Creating…' : 'Create Account'}  // ✅ 使用 loading
                onClick={handleRegister}                          // ✅ 使用 handleRegister
                //disabled={loading}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}