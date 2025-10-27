import { useState } from 'react'
import { Header } from '../../components/Header'
import { TextInput } from '../../components/TextInput'
import { PrimaryButton } from '../../components/PrimaryButton'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import illustration from '../../assets/images/illustration-admin.png'
import apiService from '../../services/api'
import AvatarPicker from "../../components/AvatarPicker"

export function SignupAdmin() {
  const [email, setEmail] = useState('')
  const [adminId, setAdminId] = useState('')          //  adminId
  const [fullName, setFullName] = useState('')        // fullName
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>('')       // 错误消息
  const [loading, setLoading] = useState<boolean>(false) // 加载状态
  const [avatarFile, setAvatarFile] = useState<File | null>(null)

  const handleRegister = async (): Promise<void> => {
    setError('')
    if (!email || !password || !fullName || !adminId) {
      setError('PLEASE ENTER YOUR INFORMATION!')
      return
    }

    try {
      setLoading(true)
      await apiService.adm_register(
        adminId,
        fullName,
        email,
        password,
        avatarFile || undefined
      )
      alert('Successful!')
      window.location.hash = '/login-admin'
    } catch (e: any) {
      setError(e?.message || 'failed to register!')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="signup-container theme-admin">
      {/* 左侧插画区域（换成 admin 插画） */}
      <section className="illustration-panel">
        <div className="illustration-bg" />
        <img className="illustration-image" src={illustration} alt="" />
        <div className="illustration-text" style={{ top: 590 }}>
          <h2 className="h2 title">Connect with the Students</h2>
          <p className="p2 body">You can easily connect with thousands of students by using our platform.</p>
        </div>
      </section>

      {/* 右侧注册表单 */}
      <section className="role-section">
        <div className="header">
          <button className="back-btn" aria-label="Back" onClick={() => history.back()}>
            <img src={ArrowRight} width={16} height={16} alt="" style={{ transform: 'scaleX(-1)' }} />
          </button>
          <Header title="Sign Up Now" subtitle="Admin" />
        </div>

        <div className="role-section-inner" style={{ marginTop: 32 }}>
          <div className="card login-card">
            {/* 头像上传（可选） */}
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
                label="Full Name"
                placeholder="Your full name"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <TextInput
                label="Admin ID"
                placeholder="z1234567"
                value={adminId}
                onChange={e => setAdminId(e.target.value)}
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

            {/* 错误信息显示 */}
            {error && (
              <div className="form-row">
                <p style={{ color: 'red', margin: 0 }}>{error}</p>
              </div>
            )}

            <div className="form-row" style={{ marginTop: 32 }}>
              <PrimaryButton
                text={loading ? 'Creating…' : 'Create Account'}
                onClick={handleRegister}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
