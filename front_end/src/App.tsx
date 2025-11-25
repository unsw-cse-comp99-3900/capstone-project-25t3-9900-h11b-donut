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
import { AdminHome } from './pages/AdminHome'
import { AdminCourses } from './pages/AdminCourses'
import { AdminManageCourse } from './pages/AdminManageCourse'
import { AdminMonitor } from './pages/AdminMonitor'
import { AdminProgressTrend } from './pages/AdminProgressTrend'
import { AdminRiskReport } from './pages/AdminRiskReport'
import { AdminProfile } from './pages/AdminProfile'
import { ChatWindow } from './pages/ChatWindow'
import { PracticeSession } from './pages/PracticeSession'



// Login status check (local only)
function isAuthed(maxAgeMs = 30 * 60 * 1000) {
  const token = localStorage.getItem('auth_token')
  const uid = localStorage.getItem('current_user_id')
  const loginTime = parseInt(localStorage.getItem('login_time') || '0', 10)
  const expired = !loginTime || Date.now() - loginTime > maxAgeMs
  return Boolean(token && uid && !expired)
}

// Pages that need protection (prefix matching)

const PROTECTED_PREFIXES = [
  '#/student-profile',
  '#/student-home',
  '#/student-courses',
  '#/course-detail/',
  '#/student-plan',
  '#/chat-window',
]

//  Determine whether the current hash is protected
function isProtectedHash(hash: string) {
  return PROTECTED_PREFIXES.some(p => hash.startsWith(p))
}


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

  if (isProtectedHash(hash) && !isAuthed()) {
    
    localStorage.removeItem('auth_token')
    localStorage.removeItem('login_time')
    localStorage.removeItem('current_user_id')
    localStorage.removeItem('user')

    window.location.hash = '#/login-student'
    return null
  }
  if (hash.startsWith('#/admin-home')) return <AdminHome />
  if (hash.startsWith('#/admin-courses')) return <AdminCourses />
  if (hash.startsWith('#/admin-manage-course')) return <AdminManageCourse />
  if (hash.startsWith('#/admin-monitor')) return <AdminMonitor />
  if (hash.startsWith('#/admin-progress-trend')) return <AdminProgressTrend />
  if (hash.startsWith('#/admin-risk-report')) return <AdminRiskReport />
  if (hash.startsWith('#/admin-profile')) return <AdminProfile />
  if (hash.startsWith('#/student-profile')) return <StudentProfile />
  if (hash.startsWith('#/student-home')) return <StudentHome />
  if (hash.startsWith('#/student-courses')) return <StudentCourses />
  if (hash.startsWith('#/course-detail/')) return <CourseDetail />
  if (hash.startsWith('#/student-plan')) return <StudentPlan />
  if (hash.startsWith('#/chat-window')) return <ChatWindow />
  if (hash.startsWith('#/practice-session/')) {
    const parts = hash.replace('#/practice-session/', '').split('/')
    if (parts.length >= 3) {
      const [course, topic, sessionId] = parts
      return <PracticeSession course={course} topic={topic} sessionId={sessionId} />
    }
    return <div>Invalid practice session URL</div>
  }
  if (hash.startsWith('#/login-student')) return <LoginStudent />
  if (hash.startsWith('#/login-admin')) return <LoginAdmin />
  if (hash.startsWith('#/signup-student')) return <SignupStudent />
  if (hash.startsWith('#/signup-admin')) return <SignupAdmin />
  return <SignupDesktop />
}

export default App
