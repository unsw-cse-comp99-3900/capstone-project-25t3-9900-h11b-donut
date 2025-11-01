import { useEffect, useState } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import { MessageModal } from '../../components/MessageModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import Star from '../../assets/icons/star-32.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import IconHelp from '../../assets/icons/help-24.svg'
import IconBell from '../../assets/icons/bell-24.svg'
import apiService from '../../services/api'
import UserWhite from '../../assets/icons/user-24-white.svg'
import illoOrange from '../../assets/images/illustration-orange.png'
import illoStudent from '../../assets/images/illustration-student.png'
import illoAdmin from '../../assets/images/illustration-admin.png'
import { coursesStore, type Deadline, type Course } from '../../store/coursesStore'

import { preferencesStore } from '../../store/preferencesStore';

function getPlanBasedProgressByDeadlineId(deadlineId: string): number {
  // 遵循可视范围：仅遍历到“最后一个 deadline 所在周”为止
  const latest = coursesStore.getLatestDeadline();
  const now = new Date();
  const monday = new Date(now); monday.setDate(now.getDate() - ((now.getDay() || 7) - 1));
  let maxOffset = 0;
  if (latest) {
    const lm = new Date(latest);
    const lmon = new Date(lm); lmon.setDate(lm.getDate() - ((lm.getDay() || 7) - 1));
    maxOffset = Math.max(0, Math.floor((lmon.getTime() - monday.getTime()) / (7*24*60*60*1000)));
  }

  const firstDash = deadlineId.indexOf('-');
  const courseIdOfDeadline = firstDash > 0 ? deadlineId.slice(0, firstDash) : '';
  const normalizedDeadlineId = deadlineId; // `${courseId}-${numeric}`

  let total = 0, done = 0;
  for (let o = 0; o <= maxOffset; o++) {
    const items = preferencesStore.getWeeklyPlan(o) || [];
    if (!items || items.length === 0) continue;
    for (const it of items) {
      const base = it.id.replace(/-\d+$/, '');
      if (base === normalizedDeadlineId) {
        total += it.minutes;
        if (it.completed) done += it.minutes;
        continue;
      }
      const dash = base.indexOf('-');
      if (dash > 0) {
        const coursePart = base.slice(0, dash);
        const tail = base.slice(dash + 1);
        if (coursePart === courseIdOfDeadline) {
          const m = tail.match(/(\d+)$/);
          const numeric = m ? m[1] : '';
          if (numeric && `${coursePart}-${numeric}` === normalizedDeadlineId) {
            total += it.minutes;
            if (it.completed) done += it.minutes;
          }
        }
      }
    }
  }
  if (total <= 0) return 0;
  return Math.min(100, Math.round((done / total) * 100));
}

const illoMap: Record<string, string> = {
  orange: illoOrange,
  student: illoStudent,
  admin: illoAdmin,
}

export function StudentHome() {
  
  const [courses, setCourses] = useState(coursesStore.myCourses)
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  const [messageModalOpen, setMessageModalOpen] = useState(false)
  const [lessons, setLessons] = useState<Deadline[]>(coursesStore.getDeadlines())
  const [unreadMessageCount, setUnreadMessageCount] = useState(0)
  const uid = localStorage.getItem('current_user_id') || '';
const [user, setUser] = useState<any>(() => {
  if (!uid) return null;
  try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'); }
  catch { return null; }
});
  useEffect(() => {
  //  切换账号后重读 user
  if (uid) {
    try {
      setUser(JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null'));
    } catch {
      setUser(null);
    }
  } else {
    setUser(null);
  }
  if (uid) {
  preferencesStore.loadWeeklyPlans?.(uid); // 如果支持传 uid，最好显式传入
}

  const unsubCourses = coursesStore.subscribe(() => {
    setCourses([...coursesStore.myCourses]);
    const sortedDeadlines = [...coursesStore.getDeadlines()].sort((a, b) => {
      const parseTime = (dueIn: string) => {
        const isNegative = dueIn.startsWith('-');
        const cleanDueIn = isNegative ? dueIn.substring(2) : dueIn;
        const match = cleanDueIn.match(/(\d+)d\s+(\d+)h\s+(\d+)m/);
        if (match) {
          const [, days, hours, minutes] = match;
          const totalMinutes = parseInt(days) * 1440 + parseInt(hours) * 60 + parseInt(minutes);
          return isNegative ? Number.POSITIVE_INFINITY : totalMinutes;
        }
        return Number.POSITIVE_INFINITY;
      };
      return parseTime(a.dueIn) - parseTime(b.dueIn);
    });
    setLessons(sortedDeadlines);
  });

  const unsubDeadlines = coursesStore.subscribe(() => {
    const parseTime = (dueIn: string) => {
      const isNegative = dueIn.startsWith('-');
      const cleanDueIn = isNegative ? dueIn.substring(2) : dueIn;
      const match = cleanDueIn.match(/(\d+)d\s+(\d+)h\s+(\d+)m/);
      if (!match) return Number.POSITIVE_INFINITY;
      const [, d, h, m] = match;
      const total = parseInt(d) * 1440 + parseInt(h) * 60 + parseInt(m);
      return isNegative ? Number.POSITIVE_INFINITY : total;
    };
    const sortedDeadlines = [...coursesStore.getDeadlines()].sort((a, b) => parseTime(a.dueIn) - parseTime(b.dueIn));
    setLessons(sortedDeadlines);
  });

  // 订阅计划变化，打勾后立即刷新 Deadlines 显示
  const unsubscribePrefs = preferencesStore.subscribe?.(() => {
    const parseTime = (dueIn: string) => {
      const isNegative = dueIn.startsWith('-');
      const cleanDueIn = isNegative ? dueIn.substring(2) : dueIn;
      const match = cleanDueIn.match(/(\d+)d\s+(\d+)h\s+(\d+)m/);
      if (!match) return Number.POSITIVE_INFINITY;
      const [, d, h, m] = match;
      const total = parseInt(d) * 1440 + parseInt(h) * 60 + parseInt(m);
      return isNegative ? Number.POSITIVE_INFINITY : total;
    };
    const sortedDeadlines = [...coursesStore.getDeadlines()].sort((a, b) => parseTime(a.dueIn) - parseTime(b.dueIn));
    setLessons(sortedDeadlines);
  });

  return () => {
    unsubCourses();
    unsubDeadlines();
  };
}, [uid]); // ★ 关键：依赖 uid
  // 每分钟刷新一次，保证倒计时实时更新并按倒计时升序展示
  useEffect(() => {
  if (!uid) return;

  if (coursesStore.myCourses.length === 0) {
    void coursesStore.refreshMyCourses();        // ✅ 没数据就拉一次
  }
  if (coursesStore.availableCourses.length === 0) {
    void coursesStore.refreshAvailableCourses(true); // ✅ 搜索页依赖的目录也拉
  }
}, [uid]);


  // 页面加载时获取未读消息数量
  useEffect(() => {
    const loadUnreadMessageCount = async () => {
      try {
        const messages = await apiService.getMessages();
        const unreadCount = messages.filter(msg => !msg.isRead).length;
        setUnreadMessageCount(unreadCount);
      } catch (error) {
        console.error('Failed to load the number of unread messages:', error);
      }
    };

    loadUnreadMessageCount();
  }, []);

  useEffect(() => {
    const parseTime = (dueIn: string) => {
      const isNegative = dueIn.startsWith('-');
      const clean = isNegative ? dueIn.substring(2) : dueIn;
      const match = clean.match(/(\d+)d\s+(\d+)h\s+(\d+)m/);
      if (!match) return Number.POSITIVE_INFINITY;
      const [, d, h, m] = match;
      const total = parseInt(d) * 1440 + parseInt(h) * 60 + parseInt(m);
      return isNegative ? Number.POSITIVE_INFINITY : total;
    };
    const refresh = () => {
      const sorted = [...coursesStore.getDeadlines()].sort((a, b) => parseTime(a.dueIn) - parseTime(b.dueIn));
      setLessons(sorted);
    };
    const timer = setInterval(refresh, 60 * 1000);
    // 首次也刷新一次，避免初次静态值
    refresh();
    return () => clearInterval(timer);
  }, [])

  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
  try { await apiService.logout(); }
  finally {
    window.location.hash = '#/login-student';
    setLogoutModalOpen(false);
  }
};

  return (
  
    <div key={uid} className="student-home-layout">
      <aside className="sh-sidebar">
        <div className="sh-profile-card" onClick={() => (window.location.hash = '#/student-profile')} role="button" aria-label="Open profile" style={{cursor:'pointer'}}>
          <div className="avatar"><img
    src={user?.avatarUrl || AvatarIcon}
    width={48}
    height={48}
    alt="avatar"
    style={{ borderRadius: '50%', objectFit: 'cover' }}
    onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
  />
  </div>
          <div className="info">
            <div className="name">{user.name}</div>
            <div className="studentId">{user.studentId}</div>
          </div>
          <button className="chevron" aria-label="Profile">
            <img src={ArrowRight} width={16} height={16} alt="" />
          </button>
        </div>

        <nav className="sh-nav">
          <a className="item active" href="#/student-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/student-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item" href="#/student-plan">
            <img src={IconSettings} className="nav-icon" alt="" /> My plan
          </a>
        </nav>

        <div className="sh-ai-card">
          <div className="ai-icon"><img src={UserWhite} width={24} height={24} alt="" /></div>
          <div className="ai-title">AI Coach</div>
          <div className="ai-sub">Chat with your AI Coach!</div>
          <button className="btn-primary ghost ai-start" onClick={() => window.location.hash = '#/chat-window'}>
            <span className="spc"></span>
            <span className="label">Start Chat</span>
            <img src={ArrowRight} width={16} height={16} alt="" className="chev" />
          </button>
        </div>

        <button className="btn-outline" onClick={handleLogout}>Log Out</button>
      </aside>

      <main className="sh-main">
        <header className="sh-header">
          <div className="left">
            <div className="hello">Hello,</div>
            <h1 className="title">{user?.name ?? ''} <span className="wave" aria-hidden>👋</span></h1>
          </div>
          <div className="right global-actions">
            <button className="icon-btn" aria-label="Help"><img src={IconHelp} width={20} height={20} alt="" /></button>
            <button className="icon-btn message-btn" aria-label="Notifications" onClick={() => setMessageModalOpen(true)}>
              <img src={IconBell} width={20} height={20} alt="" />
              {unreadMessageCount > 0 && <span className="message-badge">{unreadMessageCount}</span>}
            </button>
          </div>
        </header>

        <section className="sh-courses-section">
          <div className="section-title">Courses <span aria-hidden>😉</span></div>

          {courses.length === 0 ? (
            <div className="courses-empty">
              <div className="title">No courses found yet.</div>
              <div className="sub">Go to 'My Courses' to add your own courses!</div>
            </div>
          ) : (
            <div className="courses-grid">
              {courses.map((c) => (
                <article 
                  key={c.id} 
                  className="course-card"
                  onClick={() => window.location.hash = `#/course-detail/${c.id}`}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="thumb">
                    <img src={illoMap[c.illustration]} alt="" />
                  </div>
                  <div className="meta">
                    {'dueIn' in c && <div className="due">{(c as unknown as Deadline).dueIn}</div>}
                    <div className="name">{c.id}</div>
                    <div className="desc">{('title' in c) ? (c as unknown as Course).title : ''}</div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      <aside className="sh-lessons">
        <div className="section-title">Deadlines <span aria-hidden>📚</span></div>
        <div className="lessons-list-container">
          <div className="lessons-list">
            {lessons.map((l) => {
              const planProgress = getPlanBasedProgressByDeadlineId(l.id);
              const pct = planProgress; // 完全跟随计划勾选
              return (
                <article key={l.id} className="lesson-card">
                  <div className="icon" style={{ background: l.color, boxShadow: `0 6px 16px ${l.color}33` }}>
                    <img src={Star} width={24} height={24} alt="" />
                  </div>
                  <div className="content">
                    <div className="due">{l.dueIn}</div>
                    <div className="title">{l.course} {l.title}</div>
                    <div className="bar">
                      <div className="fill" style={{ width: `${pct}%`, background: l.color }} />
                    </div>
                  </div>
                  <div className="percent">{pct}%</div>
                </article>
              );
            })}
          </div>
        </div>
      </aside>

      <style>{css}</style>

      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={confirmLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Confirm"
        cancelText="Cancel"
      />

      <MessageModal
        isOpen={messageModalOpen}
        onClose={() => setMessageModalOpen(false)}
        onUnreadCountChange={setUnreadMessageCount}
      />
    </div>

  )
}

/* 贴近 Figma 的排版/配色/间距 */
const css = `
:root{
  --sh-border: #EAEAEA;
  --sh-muted: #6D6D78;
  --sh-text: #172239;
  --sh-card-bg:#FFFFFF;
  --sh-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --sh-orange: #F6B48E; /* 卡片主色更贴近 Figma 的桃橙 */
}

.student-home-layout{
  display:grid;
  grid-template-columns: 280px 1fr 380px;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh; /* 让布局至少占满一屏，便于侧栏拉伸 */
}

.sh-sidebar{
  display:flex;
  flex-direction:column;
  gap:24px;
  height: 100%;
}

/* 侧栏-用户卡 */
.sh-profile-card{
  display:flex;align-items:center;gap:12px;
  padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:var(--sh-card-bg);box-shadow:var(--sh-shadow);
}
.sh-profile-card .avatar{
  width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--sh-border);
}
.sh-profile-card .info .name{font-size:14px;font-weight:700}
.sh-profile-card .info .email{color:var(--sh-muted);font-size:12px}
.sh-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--sh-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center}

/* 侧栏-导航 */
.sh-nav{
  display:flex;flex-direction:column;gap:12px;
  padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);
}
.sh-nav .item{
  display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--sh-muted);text-decoration:none;font-weight:500;
}
.sh-nav .item.active{background:#FFA87A;color:#172239;font-weight:800;border-radius:20px}
.sh-nav .nav-icon{width:20px;height:20px}

/* AI Coach 卡 */
.sh-ai-card{
  padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);
  display:flex;flex-direction:column;align-items:center;text-align:center;gap:28px;
  flex: 1; min-height: 280px; /* 更小但更整齐 */
}
.sh-ai-card .ai-title{font-weight:800;font-size:18px}
.sh-ai-card .ai-sub{color:var(--sh-muted);font-size:14px}
.sh-ai-card .ai-icon{width:56px;height:56px;border-radius:14px;background:#4A90E2;display:grid;place-items:center}
.sh-ai-card .ai-icon img{filter:none}
.icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center}
.btn-primary.ghost{
  margin-top:px;display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;cursor:pointer;font-weight:800;font-size:16px;
  width:100%; min-width:unset;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease;
}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-outline{
  padding:14px;border-radius:14px;background:#fff;border:1px solid var(--sh-border);cursor:pointer;font-weight:600;
  margin-top: auto; /* 将 Log Out 固定在侧栏底部 */
}

/* 顶部标题 */
.sh-main{display:flex;flex-direction:column;gap:24px}
.sh-header{display:flex;align-items:center;justify-content:space-between}
.sh-header .hello{color:var(--sh-muted);font-size:16px}
.sh-header .title{font-size:32px;line-height:1.2;margin:4px 0 0;font-weight:700}
.sh-header .right{display:flex;align-items:center;gap:12px} /* 使右上角按钮水平并排 */
.sh-header .icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center;position:relative}

/* 消息按钮小红点样式 */
.message-btn {
  position: relative;
}

.message-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #FF6B35;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 10px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Courses */
.section-title{font-weight:800;margin-bottom:12px;font-size:22px}
.courses-grid{display:grid;grid-template-columns:repeat(auto-fill, 280px);gap:20px}
.course-card{
  display:flex;flex-direction:column;width:280px;height:320px;border:1px solid var(--sh-border);border-radius:16px;background:#fff;box-shadow:var(--sh-shadow);padding:0;overflow:hidden;cursor:pointer;
  transition: all 0.2s ease;
}
.course-card:hover{
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.course-card .thumb{
  width:100%;height:140px;background:linear-gradient(135deg, #FFA87A 0%, #FF8A5C 100%);overflow:hidden;display:grid;place-items:center;position:relative;
}
.course-card .thumb img{width:120%;height:auto;object-fit:cover}
.course-card .meta{padding:16px;flex:1;display:flex;flex-direction:column;justify-content:space-between}
.course-card .meta .due{color:#6D6D78;font-size:11px;font-weight:500;margin-bottom:6px}
.course-card .meta .name{font-weight:800;font-size:18px;line-height:1.3;color:#172239;margin-bottom:6px}
.course-card .meta .desc{color:#6D6D78;font-size:14px;line-height:1.4;margin-bottom:12px}

/* Lessons 右栏 */
.sh-lessons{padding-top:72px}
.sh-courses-section{margin-top:16px}

.lessons-list-container{
  /* 提升可见卡片数量：更高的滚动区域 + 更小的外边距 */
  max-height: calc(100vh - 180px);
  overflow-y: auto;
  margin-top: 8px;
}

.lessons-list-container::-webkit-scrollbar {
  width: 6px;
}

.lessons-list-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.lessons-list-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 10px;
}

.lessons-list-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.lessons-list{display:flex;flex-direction:column;gap:12px}

.courses-empty{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:8px;padding:150px;border:none;border-radius:0;background:#transparent;color:var(--sh-muted);
}
.courses-empty .title{font-weight:800;font-size:20px;color:#172239}
.courses-empty .sub{font-size:16px}
.lesson-card{
  display:grid;grid-template-columns:48px 1fr auto;gap:12px;align-items:center;
  padding:12px;border:1px solid var(--sh-border);border-radius:18px;background:#fff;box-shadow:var(--sh-shadow);
}
.lesson-card .icon{width:48px;height:48px;border-radius:12px;display:grid;place-items:center}
.lesson-card .content .due{color:var(--sh-muted);font-size:12px}
.lesson-card .content .title{font-weight:700;margin:4px 0 10px;font-size:16px}
.lesson-card .content .bar{height:5px;border-radius:999px;background:#F0F2F6;overflow:hidden}
.lesson-card .content .bar .fill{height:100%}
.lesson-card .percent{color:var(--sh-muted);font-weight:700}

/* Start Chat 按钮（图二样式） */
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}

.global-actions{position:fixed;top:32px;right:32px;z-index:10;display:flex;gap:12px}
@media (max-width: 1200px){
  .student-home-layout{grid-template-columns:240px 1fr;grid-template-areas:'side main' 'side lessons'}
  .sh-lessons{grid-column:1/-1}
}
`