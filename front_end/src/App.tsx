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


// 登录状态检查（只用本地）
function isAuthed(maxAgeMs = 30 * 60 * 1000) {
  const token = localStorage.getItem('auth_token')
  const uid = localStorage.getItem('current_user_id')
  const loginTime = parseInt(localStorage.getItem('login_time') || '0', 10)
  const expired = !loginTime || Date.now() - loginTime > maxAgeMs
  return Boolean(token && uid && !expired)
}

// 需要保护的页面（前缀匹配）
const PROTECTED_PREFIXES = [
  '#/student-profile',
  '#/student-home',
  '#/student-courses',
  '#/course-detail/',
  '#/student-plan',
]

//  判断当前 hash 是否受保护
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

  //  路由保护：受保护页但未登录 -> 跳转登录页
  if (isProtectedHash(hash) && !isAuthed()) {
    
    localStorage.removeItem('auth_token')
    localStorage.removeItem('login_time')
    localStorage.removeItem('current_user_id')
    localStorage.removeItem('user')

    // 跳转到登录页
    window.location.hash = '#/login-student'
    return null
  }
  if (hash.startsWith('#/admin-home')) return <AdminHome />
  if (hash.startsWith('#/admin-courses')) return <AdminCourses />
  if (hash.startsWith('#/admin-manage-course')) return <AdminManageCourse />
  if (hash.startsWith('#/admin-monitor')) return <AdminMonitor />
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
