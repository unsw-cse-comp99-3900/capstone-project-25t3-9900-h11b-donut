import { useState } from 'react'
import illustration from '../../assets/images/illustration-orange.png'
import RoleIconUser from '../../assets/icons/role-icon-64.svg'
import StarIcon from '../../assets/icons/star-32.svg'
import { Header } from '../../components/Header'
import { RoleCard } from '../../components/RoleCard'
import { PrimaryButton } from '../../components/PrimaryButton'


export function SignupDesktop() {
  const [role, setRole] = useState<'student' | 'admin' | null>('student')

  return (
    <div className="signup-container">
      <section className="illustration-panel">
        <div className="illustration-bg" />

        <div className="illustration-text">
          <h2 className="h2 title">Start Generating Your Plan</h2>
          <p className="p2 body">Learn almost any skill from a comfort of your home with our app.</p>
        </div>

        <img className="illustration-image" src={illustration} alt="Illustration" />
      </section>

      <section className="role-section">
        <div className="header">
          <Header
            title="Select Your Role"
            subtitle="Choose how you want to use the platform."
          />
        </div>

        <div className="role-section-inner">
          <div className="select-grid">
            <RoleCard
              title="Student"
              body="You are a student planning to take courses and manage your learning schedule."
              selected={role === 'student'}
              onClick={() => setRole('student')}
              iconSrc={RoleIconUser}
              badgeBg="#FFE1CF"
              badgeBorder="#F7D2C0"
            />

            <RoleCard
              title="Admin"
              body="You are an admin planning to create courses, assign tasks, and track student performance."
              selected={role === 'admin'}
              onClick={() => setRole('admin')}
              iconSrc={StarIcon}
              badgeBg="#E8D7E6"
              badgeBorder="#DAC6D8"
            />
          </div>

          <div className="actions">
            <PrimaryButton
              text="Continue"
              onClick={() => {
                if (!role) return alert('Please select a role')
                window.location.hash = role === 'admin' ? '/login-admin' : '/login-student'
              }}
            />

          </div>
        </div>
      </section>
    </div>
  )
}