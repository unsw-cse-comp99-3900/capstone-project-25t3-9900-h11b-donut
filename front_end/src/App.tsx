import './index.css'
import { useEffect, useSyncExternalStore } from 'react'
import { SignupDesktop } from './pages/SignupDesktop'
import { LoginStudent } from './pages/LoginStudent'
import { LoginAdmin } from './pages/LoginAdmin'
import { SignupStudent } from './pages/SignupStudent'
import { SignupAdmin } from './pages/SignupAdmin'
import { StudentHome } from './pages/StudentHome'
import { StudentProfile } from './pages/StudentProfile'
import { StudentCourses } from './pages/StudentCourses'
import { CourseDetail } from './pages/CourseDetail'
import { StudentPlan } from './pages/StudentPlan'

function useHash() {
  const subscribe = (cb: () => void) => {
    window.addEventListener('hashchange', cb)
    return () => window.removeEventListener('hashchange', cb)
  }
  const get = () => window.location.hash || '#/signup'
  return useSyncExternalStore(subscribe, get, get)
}

function App() {
  const hash = useHash()

  useEffect(() => {
    if (!window.location.hash) window.location.hash = '#/signup'
  }, [])

  if (hash.startsWith('#/student-profile')) return <StudentProfile />
  if (hash.startsWith('#/student-home')) return <StudentHome />
  if (hash.startsWith('#/student-courses')) return <StudentCourses />
  if (hash.startsWith('#/course-detail/')) return <CourseDetail />
  if (hash.startsWith('#/student-plan')) return <StudentPlan />
  if (hash.startsWith('#/login-student')) return <LoginStudent />
  if (hash.startsWith('#/login-admin')) return <LoginAdmin />
  if (hash.startsWith('#/signup-student')) return <SignupStudent />
  if (hash.startsWith('#/signup-admin')) return <SignupAdmin />
  return <SignupDesktop />
}

export default App