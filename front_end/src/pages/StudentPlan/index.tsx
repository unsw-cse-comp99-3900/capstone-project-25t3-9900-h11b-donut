import { useState, useEffect } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'

// 定义用户类型接口
interface User {
  name?: string;
  studentId?: string;
  avatarUrl?: string;
  email?: string;
}
import { MessageModal } from '../../components/MessageModal'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import IconHelp from '../../assets/icons/help-24.svg'
import IconBell from '../../assets/icons/bell-24.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import UserWhite from '../../assets/icons/user-24-white.svg'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import { preferencesStore, type Preferences, type PlanItem } from '../../store/preferencesStore'
import { coursesStore } from '../../store/coursesStore'
import { apiService } from '../../services/api';
import { fetchAndMapAiPlan } from '../../services/aiPlanService';
import { reportOverdueForYesterday } from '../../utils/overdueReport';

export function StudentPlan() {
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [showPrefs, setShowPrefs] = useState(false)
  const [messageModalOpen, setMessageModalOpen] = useState(false)
  const [unreadMessageCount, setUnreadMessageCount] = useState(0)
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  
  const uid = localStorage.getItem('current_user_id');
  let user: User = {};

  if (uid) {
    try {
      user = JSON.parse(localStorage.getItem(`u:${uid}:user`) || '{}') as User;
    } catch {
      user = {};
    }
  } else {
    // 没有 current_user_id，说明未登录
    user = {};
  }
  // Initialize local form state from global preferences
  const init = preferencesStore.getPreferences()
  const [dailyHours, setDailyHours] = useState(init.dailyHours)
  const [weeklyStudyDays, setWeeklyStudyDays] = useState(init.weeklyStudyDays)
  const [avoidDays, setAvoidDays] = useState<string[]>(init.avoidDays)
  const [saveAsDefault, setSaveAsDefault] = useState(init.saveAsDefault)
  const [description, setDescription] = useState(init.description ?? '')
  const [showDays, setShowDays] = useState(false)

  // 每周计划视图
  const [showPlan, setShowPlan] = useState(false)
  const [weekOffset, setWeekOffset] = useState(0)
  const [weeklyPlan, setWeeklyPlan] = useState<Record<number, PlanItem[]>>({})

  // 计算最大可显示的周偏移量（基于最新截止日期）
  const getMaxWeekOffset = () => {
    const latestDeadline = coursesStore.getLatestDeadline();
    if (!latestDeadline) return 0; // 如果没有截止日期，只显示当前周
    
    const now = new Date();
    const currentMonday = new Date(now);
    currentMonday.setDate(now.getDate() - (now.getDay() || 7) + 1); // 当前周的周一
    
    const deadlineMonday = new Date(latestDeadline);
    deadlineMonday.setDate(latestDeadline.getDate() - (latestDeadline.getDay() || 7) + 1); // 截止日期所在周的周一
    
    // 计算周偏移量（从当前周到截止日期所在周）
    const diffTime = deadlineMonday.getTime() - currentMonday.getTime();
    const diffWeeks = Math.floor(diffTime / (1000 * 60 * 60 * 24 * 7));
    
    return Math.max(0, diffWeeks); // 确保非负数
  }
useEffect(() => {
  const uid = localStorage.getItem('current_user_id');
  if (!uid) return;

  const raw = localStorage.getItem(`u:${uid}:ai-web-weekly-plans`);
  if (raw) {
    // plan 已经生成并存在 localStorage，可以安全上报 overdue
    reportOverdueForYesterday().catch((e) => console.warn('[overdue] failed:', e));
  }
}, []);
  // 页面加载时获取未读消息数量
  useEffect(() => {
    const loadUnreadMessageCount = async () => {
      try {
        const messages = await apiService.getMessages();
        const unreadCount = messages.filter(msg => !msg.isRead).length;
        setUnreadMessageCount(unreadCount);
      } catch (error) {
        console.error('加载未读消息数量失败:', error);
      }
    };

    loadUnreadMessageCount();
  }, []);
useEffect(() => {
  coursesStore.ensureLoaded();
}, []);
  // 组件加载时从preferencesStore加载已保存的计划
  useEffect(() => {
  const savedPlan = preferencesStore.getWeeklyPlan(weekOffset);
  if (savedPlan.length > 0) {
    // 将 PlanItem[] 转换为按天分组的 Record<number, PlanItem[]>
    const planByDay: Record<number, PlanItem[]> = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]};

    savedPlan.forEach(item => {
      const itemDate = new Date(item.date);  // 不处理时区
      const dayIdx = (itemDate.getDay() + 6) % 7; // Mon=0, Tue=1, ..., Sun=6
      planByDay[dayIdx] = [...planByDay[dayIdx], item];
    });
    setWeeklyPlan(planByDay);
    setShowPlan(true);
  }
}, [weekOffset]);

  // 颜色统一由 coursesStore 提供，避免本地硬编码，便于后端对接

  const getWeekRange = (offset = weekOffset) => {
    const now = new Date()
    const day = now.getDay() || 7 // 周一=1
    const monday = new Date(now)
    monday.setDate(now.getDate() - (day - 1))
    // 应用周偏移（上一周/下一周）
    monday.setDate(monday.getDate() + offset * 7)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    return {
      monday,
      sunday,
      label: `${monday.toLocaleString('en-US',{month:'short'})} ${monday.getDate()} - ${sunday.getDate()}, ${sunday.getFullYear()}`
    }
  }

  // const generateWeeklyPlan = (offset = weekOffset): Record<number, PlanItem[]> => {
  //   // 使用 preferencesStore 生成计划数据
  //   const planItems =  preferencesStore.generateWeeklyPlan();
    
  //   // 按天分组
  //   const result: Record<number, PlanItem[]> = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]};
  //   planItems.forEach(item => {
  //     const { monday, sunday } = getWeekRange(offset);
  //     const itemDate = new Date(item.date);
  //     // 过滤掉不在当前周范围内的项
  //     if (itemDate < monday || itemDate > sunday) return;
  //     const dayDiff = Math.floor((itemDate.getTime() - monday.getTime()) / (1000 * 60 * 60 * 24));
  //     const dayIdx = Math.max(0, Math.min(6, dayDiff));
  //     result[dayIdx] = [...result[dayIdx], item];
  //   });

  //   return result;
  // }

  const days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

  const toggleAvoid = (d: string) => {
    setAvoidDays(prev => prev.includes(d) ? prev.filter(i => i !== d) : [...prev, d])
  }

  const applyPreferences = async () => {
    if (isGeneratingPlan) return; // 防止重复点击
    setIsGeneratingPlan(true); // 开始加载
    
    const toSave: Partial<Preferences> = {
    dailyHours: Math.max(1, Math.min(12, Number(dailyHours) || 1)),
    weeklyStudyDays: Math.max(1, Math.min(7, Number(weeklyStudyDays) || 1)),
    avoidDays,
    saveAsDefault,
    description
  }
  const check = preferencesStore.validatePreferences(toSave as Preferences);
  if (!check.isValid) {
    alert(check.errors.join('\n'));

    return;
  }
  await preferencesStore.setPreferences(toSave)

  try {
    // 清除旧的AI计划缓存，确保获取最新的Gemini生成数据
    const uid = localStorage.getItem('current_user_id');
    if (uid) {
      const cacheKey = `u:${uid}:ai-web-weekly-plans`;
      localStorage.removeItem(cacheKey);
      console.log('🗑️ 已清除AI计划缓存，将重新生成');
    }
    
    console.log('🚀 开始生成AI计划，期望看到Gemini生成的特定标题...');
    
    // 1) 后端生成 + 映射
    const weeklyPlan = await fetchAndMapAiPlan();
    console.log('✅ 转换后的 WeeklyPlan:', weeklyPlan);

    // 检查是否成功获取到计划数据
    if (!weeklyPlan || Object.keys(weeklyPlan).length === 0) {
      console.warn('⚠️ AI计划为空，使用本地fallback');
      alert('AI计划生成暂时不可用，请稍后重试或联系管理员。');
      return;
    }

    // 2) 写入 store
    preferencesStore.setWeeklyPlan(0, weeklyPlan[0] || []);
    for (const [offsetStr, items] of Object.entries(weeklyPlan)) {
      preferencesStore.setWeeklyPlan(Number(offsetStr), items);
    }

    //  3) 立刻把"本周"的 PlanItem[] 分桶并喂给组件状态（不等 useEffect）
    const cur = preferencesStore.getWeeklyPlan(0) || [];
    const planByDay: Record<number, PlanItem[]> = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]};
    for (const it of cur) {
      const d = new Date(it.date);                  // 按你要求：不考虑时区
      const dayIdx = (d.getDay() + 6) % 7;          // Mon=0..Sun=6
      planByDay[dayIdx] = [...planByDay[dayIdx], it];
    }
    setWeekOffset(0);
    setWeeklyPlan(planByDay);

    // 4) 再切界面（此时 state 已就绪，页面立即有内容）
    setShowPlan(true);
    setShowPrefs(false);

  } catch (err) {
    console.error('❌ AI 计划失败:', err);
    alert(`AI计划生成失败: ${err instanceof Error ? err.message : '未知错误'}。请检查网络连接或稍后重试。`);
    return;
  } finally {
    setIsGeneratingPlan(false); // 结束加载
  }
};
  
  return (
    <div className="student-plan-layout">
      {/* Left sidebar — exactly same size/position as StudentHome */}
      <aside className="sh-sidebar">
        <div
          className="sh-profile-card"
          onClick={() => (window.location.hash = '#/student-profile')}
          role="button"
          aria-label="Open profile"
          style={{ cursor: 'pointer' }}
        >
          <div className="avatar"><img
    src={user?.avatarUrl || AvatarIcon}
    width={48}
    height={48}
    alt="avatar"
    style={{ borderRadius: '50%', objectFit: 'cover' }}
    onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
  /></div>
          <div className="info">
            <div className="name">{user?.name || 'Student'}</div>
            <div className="studentId">{user?.studentId || 'ID'}</div>
          </div>
          <button className="chevron" aria-label="Profile">
            <img src={ArrowRight} width={16} height={16} alt="" />
          </button>
        </div>

        <nav className="sh-nav">
          <a className="item" href="#/student-home">
            <img src={IconHome} className="nav-icon" alt="" /> Home
          </a>
          <a className="item" href="#/student-courses">
            <img src={IconCourses} className="nav-icon" alt="" /> My Courses
          </a>
          <a className="item active" href="#/student-plan">
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

        <button className="btn-outline" onClick={() => setShowLogoutConfirm(true)}>Log Out</button>
      </aside>

      {/* Middle content */}
      <main className="sp-main">
        <div className="sp-actions global-actions">
          <button className="icon-btn" aria-label="Help"><img src={IconHelp} width={20} height={20} alt="" /></button>
          <button className="icon-btn message-btn" aria-label="Notifications" onClick={() => setMessageModalOpen(true)}>
            <img src={IconBell} width={20} height={20} alt="" />
            {unreadMessageCount > 0 && <span className="message-badge">{unreadMessageCount}</span>}
          </button>
        </div>

        <div className="sp-generate-bar">
          <button className="btn-generate" onClick={() => setShowPrefs(true)}>{showPlan ? 'Reschedule Plan' : 'Generate Plan'}</button>
        </div>

        <section className={`sp-board ${showPlan ? 'has-plan' : ''}`}>
          {showPlan ? (
            <div className="sp-week">
              <div className="sp-week-header">
                <span>{getWeekRange(weekOffset).label}</span>
                <div className="sp-week-nav">
                  <button className="week-btn" aria-label="Previous week" disabled={weekOffset <= 0} onClick={() => { 
                    if (weekOffset <= 0) return;
                    const n = weekOffset - 1;
                    setWeekOffset(n);
                    const items = preferencesStore.getWeeklyPlan(n) || [];

                    const planByDay: Record<number, PlanItem[]> = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]};
                    for (const item of items) {
                      const d = new Date(item.date);               // 不处理时区
                      const dayIdx = (d.getDay() + 6) % 7;         // Mon=0 ... Sun=6
                      planByDay[dayIdx] = [...planByDay[dayIdx], item];
                    }
                    setWeeklyPlan(planByDay);
                    
                  }}>‹</button>
                  <button className="week-btn" aria-label="Next week" disabled={weekOffset >= getMaxWeekOffset()} onClick={() => { 
                    const maxOffset = getMaxWeekOffset();
                    if (weekOffset >= maxOffset) return;
                    const n = weekOffset + 1; 
                    setWeekOffset(n); 
                     const items = preferencesStore.getWeeklyPlan(n) || [];

                    const planByDay: Record<number, PlanItem[]> = {0:[],1:[],2:[],3:[],4:[],5:[],6:[]};
                    for (const item of items) {
                      const d = new Date(item.date);               // 不处理时区
                      const dayIdx = (d.getDay() + 6) % 7;         // Mon=0 ... Sun=6
                      planByDay[dayIdx] = [...planByDay[dayIdx], item];
                    }
                    setWeeklyPlan(planByDay);


                     
                  }}>›</button>
                </div>
              </div>
              <div className="sp-week-body">
              {[0,1,2,3,4,5,6].map((dIdx) => {
                const base = getWeekRange(weekOffset).monday
                const day = new Date(base); day.setDate(base.getDate() + dIdx)
                const dayLabel = day.toLocaleString('en-US', { weekday:'short'})
                const dayNum = day.getDate()
                const items = weeklyPlan[dIdx] || []
                return (
                  <div key={dIdx} className="sp-day">
                    <div className="sp-day-left">
                      <div className="dow">{dayLabel}</div>
                      <div className="dom">{dayNum}</div>
                    </div>
                    <div className="sp-day-items">
                      {items.length === 0 ? (
                        <div className="empty"></div>
                      ) : items.map((it, i) => (
                        <label key={it.id+'-'+i} className="wp-item">
                          <input
                            type="checkbox"
                            checked={!!it.completed}
                            onChange={(e) => {
                              const checked = e.target.checked;
                              setWeeklyPlan(prev => {
                                const clone: Record<number, PlanItem[]> = { ...prev };
                                clone[dIdx] = (clone[dIdx] || []).map(ci => ci === it ? { ...ci, completed: checked } : ci);

                                // 基于"任务"维度计算进度（跨所有周累计分钟数）
                                const prefix = `${it.courseId}-`;
                                let extracted = it.id.startsWith(prefix) ? it.id.slice(prefix.length) : it.id;
                                extracted = extracted.replace(/-\d+$/, '');
                                const baseKey = `${it.courseId}-${extracted}`; // deadline key

                                // 1) 计算该任务 totalMinutes（遍历 0..maxOffset 的所有周）
                                const maxOffset = getMaxWeekOffset();
                                let totalMinutes = 0;
                                for (let o = 0; o <= maxOffset; o++) {
                                  const items = preferencesStore.getWeeklyPlan(o) || [];
                                  for (const p of items) {
                                    if (p.id.startsWith(baseKey)) totalMinutes += p.minutes;
                                  }
                                }
                                // 把当前周的 clone 覆盖回当前 offset，保证本次勾选立即生效
                                const mergedItemsNow = Object.values(clone).flat();
                                const otherWeeks: PlanItem[] = [];
                                for (let o = 0; o <= maxOffset; o++) {
                                  if (o === weekOffset) continue;
                                  otherWeeks.push(...(preferencesStore.getWeeklyPlan(o) || []));
                                }
                                const allItems = [...otherWeeks, ...mergedItemsNow];

                                // 2) 计算 completedMinutes（使用最新勾选状态）
                                let completedMinutes = 0;
                                for (const p of allItems) {
                                  if (p.id.startsWith(baseKey) && p.completed) {
                                    completedMinutes += p.minutes;
                                  }
                                }
                                const progress = totalMinutes > 0 ? Math.min(100, Math.round((completedMinutes / totalMinutes) * 100)) : 0;

                                // 同步 Deadlines 进度（按比例更新）
                                coursesStore.setProgress(baseKey, progress);

                                // 保存更新后的"当前周"计划到 localStorage
                                const planItemsCurrentWeek = mergedItemsNow;
                                preferencesStore.setWeeklyPlan(weekOffset, planItemsCurrentWeek);

                                return clone;
                              });

                              // 调试输出课程整体进度
                              const courseProgress = coursesStore.getCourseProgress(it.courseId);
                              console.log(`Course ${it.courseId} progress: ${courseProgress}%`);
                            }}
                          />
                          
                          <div className="wp-meta">
                            <div className="wp-time">~ {it.minutes} min</div>
                            <div className="wp-title">{it.courseTitle}</div>
                            <div className="wp-sub">{it.partTitle}</div>
                            <div className="wp-task-progress">
                              <div className="wp-progress">
                                <div className="bar"><span style={{ width: (it.completed ? 100 : 0) + '%', background: it.color }} /></div>
                                <div className="pct">{it.completed ? '100%' : '0%'}</div>
                              </div>
                              <div className="wp-part-percent">Part: {(() => {
                                // 从 id 中稳健解析 taskId：去掉课程前缀，再去掉末尾的 -partIndex
                                const prefix = `${it.courseId}-`;
                                let taskId = it.id.startsWith(prefix) ? it.id.slice(prefix.length) : it.id;
                                taskId = taskId.replace(/-\d+$/, '');

                                const maxOffset = getMaxWeekOffset();
                                let totalMinutes = 0;
                                for (let o = 0; o <= maxOffset; o++) {
                                  const items = preferencesStore.getWeeklyPlan(o) || [];
                                  for (const p of items) {
                                    if (p.id.startsWith(`${it.courseId}-${taskId}`)) totalMinutes += p.minutes;
                                  }
                                }
                                const partPercent = totalMinutes > 0 ? Math.round((it.minutes / totalMinutes) * 100) : 0;
                                return `${partPercent}%`;
                              })()}</div>
                            </div>
                          </div>
                          
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            </div>
          ) : (
            <div className="sp-placeholder">
              <div className="sp-empty-title">When you have a deadline,</div>
              <div className="sp-empty-sub">click 'Generate' button above to get your own plan!</div>
            </div>
          )}
        </section>
      </main>

      {/* Preferences Modal */}
      {showPrefs && (
        <>
          <div className="sp-modal-mask" onClick={() => setShowPrefs(false)} />
          <div className="sp-modal" role="dialog" aria-modal="true" aria-labelledby="sp-prefs-title">
            <button className="sp-back" aria-label="Close" onClick={() => setShowPrefs(false)}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 14L5 8L11 2" stroke="#161616" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <h2 id="sp-prefs-title" className="sp-modal-title">Preferences 📚</h2>

            <div className="sp-field">
              <label>Daily Hours:</label>
              <input type="number" min="1" max="12" value={dailyHours} onChange={e => setDailyHours(Number(e.target.value))} />
            </div>

            <div className="sp-field">
              <label>Weekly Study Days:</label>
              <input type="number" min="1" max="7" value={weeklyStudyDays} onChange={e => setWeeklyStudyDays(Number(e.target.value))} />
            </div>

            <div className="sp-field sp-field-col">
              <label>Avoid Days:</label>
              <div className="sp-dropdown">
                <button type="button" className="sp-dropdown-btn" onClick={() => setShowDays(v => !v)}>
                  {avoidDays.length === 0 ? 'Select days' : avoidDays.join(', ')}
                  <span className="caret">▼</span>
                </button>
                {showDays && (
                  <div className="sp-dropdown-panel">
                    {days.map(d => (
                      <label key={d} className="sp-option">
                        <input type="checkbox" checked={avoidDays.includes(d)} onChange={() => toggleAvoid(d)} />
                        <span>{d}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="sp-field sp-field-col">
              <label>Description:</label>
              <textarea className="sp-textarea" rows={3} placeholder="Briefly describe your current understanding or background after reading the course outline..."
                value={description} onChange={e => setDescription(e.target.value)} />
            </div>

            <label className="sp-checkbox">
              <input type="checkbox" checked={saveAsDefault} onChange={e => setSaveAsDefault(e.target.checked)} />
              <span>Save as default</span>
            </label>

            <button className="btn-primary ghost ai-start sp-apply-mini" onClick={applyPreferences}>
              <span className="spc"></span>
              <span className="label">{isGeneratingPlan ? "Generating..." : "Apply"}</span>
              <img src={ArrowRight} width={16} height={16} alt="" className="chev" />
            </button>
          </div>
        </>
      )}

      <style>{css}</style>

      {showLogoutConfirm && (
        <ConfirmationModal
            isOpen={showLogoutConfirm}
            onClose={() => setShowLogoutConfirm(false)}
            onConfirm={async () => {
              setShowLogoutConfirm(false);

              await apiService.logout();

              window.location.hash = '#/login-student';
            }}
            title="Log Out"
            message="Are you sure you want to log out?"
            confirmText="Confirm"
            cancelText="Cancel"
          />
      )}

      <MessageModal
        isOpen={messageModalOpen}
        onClose={() => setMessageModalOpen(false)}
        onUnreadCountChange={setUnreadMessageCount}
      />
    </div>
  )
}

const css = `
:root{
  --sh-border:#EAEAEA;
  --sh-muted:#6D6D78;
  --sh-text:#172239;
  --sh-card-bg:#FFFFFF;
  --sh-shadow:0 8px 24px rgba(0,0,0,0.04);
  --sh-orange:#FFA87A;
  --sh-blue:#4A90E2;
}

.student-plan-layout{
  display:grid;
  grid-template-columns:280px 1fr;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  min-height:100vh;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}

/* Left sidebar — reuse StudentHome styles */
.sh-sidebar{display:flex;flex-direction:column;gap:24px}
.sh-profile-card{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-profile-card .avatar{width:48px;height:48px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:#F4F6FA;border:1px solid var(--sh-border)}
.sh-profile-card .info .name{font-size:14px;font-weight:700}
.sh-profile-card .info .email{font-size:12px;color:var(--sh-muted)}
.sh-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--sh-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center}
.sh-nav{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-nav .item{display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--sh-muted);text-decoration:none;font-weight:500}
.sh-nav .item.active{background:#FFA87A;color:#172239;font-weight:800;border-radius:20px}
.sh-nav .nav-icon{width:20px;height:20px}
.sh-ai-card{padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);display:flex;flex-direction:column;align-items:center;text-align:center;gap:28px;flex:1;min-height:280px}
.sh-ai-card .ai-title{font-weight:800;font-size:18px}
.sh-ai-card .ai-sub{color:var(--sh-muted);font-size:14px}
.sh-ai-card .ai-icon{width:56px;height:56px;border-radius:14px;background:var(--sh-blue);display:grid;place-items:center}
.btn-outline{padding:14px;border-radius:14px;background:#fff;border:1px solid var(--sh-border);font-weight:600;margin-top:auto}

/* Global actions (same as StudentHome) */
.icon-btn{width:40px;height:40px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;display:grid;place-items:center;position:relative}
.global-actions{position:fixed;top:32px;right:32px;z-index:10;display:flex;gap:12px;will-change:transform}

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

/* Start Chat 按钮（与 Generate 按钮一致） */
.btn-primary.ghost{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;font-weight:800;font-size:16px;width:100%;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}
.sp-apply-mini{width:auto;min-width:160px;max-width:70%;padding:12px 16px;margin:14px auto 6px auto}

/* Middle area */
.sp-main{display:flex;flex-direction:column;gap:16px}

/* Generate bar */
.sp-generate-bar{display:flex;align-items:center}
.btn-generate{
  padding:20px 36px;
  border-radius:24px;
  background:#F6B48E;
  color:#172239;
  font-weight:800;
  font-size:16px;
  border:none;
  cursor:pointer;
  box-shadow:0 6px 18px rgba(0,0,0,0.06);
  transition:all .2s ease;
}
.btn-generate:hover{background:#FFA87A;transform:translateY(-1px)}

/* Board card */
/* 空状态默认居中，保持不变 */
.sp-board{
  margin-top:10px;
  border:none;
  border-radius:0;
  background:transparent;
  box-shadow:none;
  min-height:520px;
  display:grid;
  place-items:center;
  padding:0;
}
/* 仅当存在计划时，使用拉伸布局和更高的最小高度，不影响空状态 */
.sp-board.has-plan{
  min-height:calc(100vh - 180px);
  display:block;
  padding:0;
}
.sp-placeholder{
  text-align:center;
  max-width:600px;
}
.sp-empty-title{font-weight:800;font-size:20px;color:#172239;margin-bottom:8px}
.sp-empty-sub{font-size:16px;color:#6D6D78}

/* Preferences Modal */
.sp-modal-mask{
  position:fixed;inset:0;background:rgba(0,0,0,0.2);backdrop-filter:saturate(180%) blur(2px);z-index:90;will-change:transform;
}
.sp-modal{
  position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
  width:520px;max-width:92vw;background:#fff;border-radius:20px;border:2px solid #F6B48E;
  box-shadow:0 24px 48px rgba(0,0,0,0.12);padding:28px;z-index:100;will-change:transform;
}
.sp-back{
  position:absolute;left:12px;top:12px;width:36px;height:36px;border-radius:999px;border:1px solid var(--sh-border);background:#fff;cursor:pointer;
  display:grid;place-items:center;
}
.sp-modal-title{
  text-align:center;font-weight:800;font-size:22px;margin:4px 0 16px;color:#172239;
}
.sp-field{display:flex;align-items:center;justify-content:space-between;margin:12px 0}
.sp-field.sp-field-col{align-items:flex-start;gap:12px}
.sp-textarea{flex:1;min-height:84px;resize:vertical;padding:10px 12px;border:1px solid var(--sh-border);border-radius:12px;font-weight:600;width:60%}
.sp-field label{font-weight:700;color:#172239}
.sp-field input[type="number"]{
  width:120px;padding:10px 12px;border:1px solid var(--sh-border);border-radius:12px;font-weight:700;
}
/* Dropdown multi-select for Avoid Days */
.sp-dropdown{position:relative}
.sp-dropdown-btn{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  min-width:220px;padding:10px 12px;border:1px solid var(--sh-border);border-radius:12px;background:#fff;cursor:pointer;font-weight:700;color:#172239;
}
.sp-dropdown-btn .caret{font-size:12px;color:#6D6D78}
.sp-dropdown-panel{
  position:absolute;top:110%;left:0;min-width:220px;background:#fff;border:1px solid var(--sh-border);border-radius:12px;box-shadow:0 12px 24px rgba(0,0,0,0.08);
  padding:8px;z-index:120;display:grid;grid-template-columns:repeat(2, 1fr);gap:6px;
}
.sp-option{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:8px;cursor:pointer}
.sp-option:hover{background:#F8F8FA}
.sp-checkbox{display:flex;align-items:center;gap:10px;margin-top:6px;color:#6D6D78}

/* Weekly plan */
.sp-week{width:100%;display:flex;flex-direction:column;gap:12px;margin-top:4px;min-height:calc(100vh - 228px);height:calc(100vh - 228px);overflow:hidden;padding-bottom:0}
.sp-week-body{flex:1;overflow:auto;scrollbar-gutter:stable; padding:4px 16px 8px 0; display:flex; flex-direction:column; gap:16px;}
.sp-week-header{font-weight:800;font-size:18px;text-align:center;margin-bottom:6px;color:#172239;position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:center;gap:8px;background:#fff;padding:8px 0;box-shadow:0 2px 6px rgba(0,0,0,0.04);will-change:transform}
.sp-week-nav{position:absolute;right:4px;display:flex;gap:8px}
.week-btn{width:34px;height:34px;border-radius:50%;border:1px solid #E6EAF2;background:#fff;display:grid;place-items:center;cursor:pointer;transition:all .2s ease}
.week-btn:hover{background:#f8f9fb;border-color:#DCE3EE}
.week-btn:disabled{opacity:.45;cursor:not-allowed;background:#fff;border-color:#E6EAF2}
.sp-day{display:flex;align-items:flex-start;gap:12px;padding:16px;border-radius:28px;background:#fff;border:1px solid var(--sh-border);box-shadow:0 2px 8px rgba(0,0,0,0.03);min-height:120px;height:auto;overflow:visible;flex:0 0 auto}
.sp-day-left{width:70px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.sp-day-left .dow{font-weight:700;color:#6D6D78}
.sp-day-left .dom{font-weight:800;font-size:20px;color:#172239}
.sp-day-items{flex:1;display:flex;gap:10px;flex-wrap:wrap;width:100%;align-items:flex-start;align-content:flex-start}
.wp-item{display:flex;align-items:flex-start;gap:10px;padding:10px 16px;border-radius:20px;background:#fff;border:1px solid #EFEFF2;box-shadow:0 2px 8px rgba(0,0,0,0.04);width:300px;max-width:100%;flex:0 0 auto;min-height:76px;height:auto}
.wp-item input[type="checkbox"]{width:16px;height:16px;accent-color:#172239;margin-top:2px}
.wp-item .dot{width:14px;height:14px;border-radius:999px;display:inline-block}
.wp-meta{display:flex;flex-direction:column;gap:4px;min-width:220px;flex:1}
.wp-title{font-weight:800;color:#172239}
.wp-sub{font-size:12px;color:#6D6D78}
.wp-progress{display:flex;align-items:center;gap:8px}
.wp-progress .bar{flex:1;height:6px;background:#F0F2F7;border-radius:999px;overflow:hidden}
.wp-progress .bar span{display:block;height:100%;background:#172239;border-radius:999px}
.wp-task-progress{display:flex;flex-direction:column;gap:4px}
.wp-progress{display:flex;align-items:center;gap:8px}
.wp-progress .bar{flex:1;height:6px;background:#F0F2F7;border-radius:999px;overflow:hidden}
.wp-progress .bar span{display:block;height:100%;background:#172239;border-radius:999px}
.wp-progress .pct{font-size:12px;color:#6D6D78}
.wp-part-percent{font-size:10px;color:#8B8B9A;background:#F5F5F7;padding:2px 6px;border-radius:4px;align-self:flex-start}
.wp-time{margin-left:0;font-size:12px;color:#6D6D78;background:#F8F8FA;border:1px solid #EFEFF2;padding:2px 8px;border-radius:999px;font-weight:700;align-self:flex-start}

`