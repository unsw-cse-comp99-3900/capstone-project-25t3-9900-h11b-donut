import { useEffect, useState, useRef } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import UserWhite from '../../assets/icons/user-24-white.svg'
import { preferencesStore } from '../../store/preferencesStore'

/** ChatWindow
 *  - 左侧：完全复用 StudentHome 的侧栏结构（用户卡/导航/AI卡/登出按钮）
 *  - 右侧：按设计图构建居中内容与输入框
 *  - 仅前端静态样式与交互占位，不接后端（遵循规则：数据走 API，现为占位）
 */
export function ChatWindow() {
  const uid = localStorage.getItem('current_user_id') || ''
  const [user, setUser] = useState<any>(() => {
    if (!uid) return null
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null') }
    catch { return null }
  })
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)

  useEffect(() => {
    if (uid) {
      try { setUser(JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null')) }
      catch { setUser(null) }
    } else setUser(null)

    // 与 StudentHome 一致：确保周计划预加载（不影响本页 UI）
    preferencesStore.loadWeeklyPlans?.()
  }, [uid])

  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
    try {
      // 调用后端 /api/auth/logout
      // await apiService.logout();

      // ✅ 只清除登录状态相关数据
      localStorage.removeItem('auth_token');
      localStorage.removeItem('login_time');
      localStorage.removeItem('current_user_id');
      // 清除本地 token

      console.log('User logged out');
      window.location.hash = '#/login-student'; // 跳回登录页
    } catch (e) {
      console.error('Logout failed:', e);
    } finally {
      setLogoutModalOpen(false); // 关闭弹窗
    }
  };

  const goBack = () => {
    // 简单返回上一页，若无历史则回 Home
    if (window.history.length > 1) window.history.back()
    else window.location.hash = '#/student-home'
  }

  const [showChat, setShowChat] = useState(false)
  const [chatMessages, setChatMessages] = useState<any[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const messagesRef = useRef<HTMLDivElement | null>(null) // 聊天消息容器引用，用于自动滚动
  const [practiceOpen, setPracticeOpen] = useState(false)
  // 练习阶段状态：intro（介绍）或 quiz（答题）
  const [practiceStage, setPracticeStage] = useState<'intro' | 'quiz'>('intro')
  // 占位题库（前端 mock，不接后端）- 包含选择题和简答题
  const quizQuestions = [
    { 
      type: 'multiple-choice' as const,
      q: 'What is the time complexity of binary search?', 
      options: ['O(n)', 'O(log n)', 'O(1)', 'O(n^2)'], 
      correct: 1 
    },
    { 
      type: 'multiple-choice' as const,
      q: 'Which data structure is best for FIFO?', 
      options: ['Stack', 'Queue', 'Tree', 'Graph'], 
      correct: 1 
    },
    { 
      type: 'essay' as const,
      q: 'Explain the difference between stack and queue data structures.',
      placeholder: 'Write your answer here...'
    },
    { 
      type: 'essay' as const,
      q: 'Describe how binary search works and when it should be used.',
      placeholder: 'Provide a detailed explanation...'
    }
  ] as const
  const [quizIndex, setQuizIndex] = useState(0)
  const [answers, setAnswers] = useState<(number | string | null)[]>(Array(quizQuestions.length).fill(null))

  const onSend = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!currentInput.trim()) return
    
    // 保存用户输入内容，因为setTimeout回调中currentInput已经为空
    const userInput = currentInput.trim()
    
    // 进入聊天态
    setShowChat(true)
    
    // 添加用户消息
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userInput,
      timestamp: new Date()
    }
    
    setChatMessages(prev => [...prev, newUserMessage])
    setCurrentInput('')
    
    // 根据不同的输入内容生成对应的AI回复
    setTimeout(() => {
      let aiResponse;
      
      if (userInput.toLowerCase().includes('explain') || userInput.toLowerCase().includes('plan')) {
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                Hi! Here's a detailed explanation of your personalized learning plan.
              </div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>How your plan was created:</div>
              <ul style={{ paddingLeft: 18, margin: 0 }}>
                <li><strong>Study preferences:</strong> 3 hours per day, 5 days a week (avoiding Sundays)</li>
                <li><strong>Course deadlines:</strong> All assignments and project due dates are considered</li>
                <li><strong>Task structure:</strong> Sequential completion (Part 1 → Part 2 → Part 3) for each task</li>
                <li><strong>Learning pace:</strong> Balanced workload with regular review sessions</li>
              </ul>
              <div style={{ marginTop: 12, padding: 10, background: '#f8f9fa', borderRadius: 8 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>💡 Tip:</div>
                <div>Your plan automatically adjusts if you miss a day - it will reschedule unfinished tasks for the next available study session.</div>
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      } else if (userInput.toLowerCase().includes('practice') || userInput.toLowerCase().includes('weak') || userInput.toLowerCase().includes('topic') || userInput.toLowerCase().includes('hard')) {
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                I understand this topic feels challenging! That's completely normal. 🎯
              </div>
              <div style={{ marginBottom: 10 }}>
                Based on your progress, I've created a focused 10-minute practice session targeting the areas you're finding difficult.
              </div>
              <button
                className="cw-cta-btn"
                onClick={() => { setPracticeStage('intro'); setQuizIndex(0); setAnswers(Array(quizQuestions.length).fill(null)); setPracticeOpen(true) }}
                aria-label="Start practice"
              >
                Start 10-minute practice session
                <img src={ArrowRight} width={16} height={16} alt="" style={{ marginLeft: 8 }} />
              </button>
              <div style={{ marginTop: 12, fontSize: 13, color: '#666' }}>
                This practice will help reinforce key concepts and build your confidence!
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      } else if (userInput.toLowerCase().includes('encouragement') || userInput.toLowerCase().includes('encourage') || userInput.toLowerCase().includes('motivation')) {
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                You're doing amazing! 🌟
              </div>
              <div style={{ lineHeight: 1.6 }}>
                Learning new things can be challenging, but every step you take is building your knowledge and skills.
                <br /><br />
                Remember: Progress isn't always linear. Some days will feel easier than others, and that's perfectly okay!
                <br /><br />
                You've already shown great dedication by seeking help and working through difficult concepts. Keep going - you've got this! 💪
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      } else if (userInput.toLowerCase().includes('part') || userInput.toLowerCase().includes('task') || userInput.toLowerCase().includes('approach')) {
        // 检测具体的任务和部分
        let taskName = "Final Project Report";
        let partNumber = "2";
        
        if (userInput.toLowerCase().includes('part 1') || userInput.toLowerCase().includes('part1')) {
          partNumber = "1";
          taskName = "Research Proposal";
        } else if (userInput.toLowerCase().includes('part 3') || userInput.toLowerCase().includes('part3')) {
          partNumber = "3";
          taskName = "Presentation Preparation";
        }
        
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                Great question! Let me explain Part {partNumber} of "{taskName}" for you.
              </div>
              <div style={{ lineHeight: 1.6 }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>For Part {partNumber} of this task:</div>
                <ul style={{ paddingLeft: 18, margin: 0, marginBottom: 12 }}>
                  <li><strong>Focus on:</strong> {partNumber === "1" ? "Research question formulation and literature review" : partNumber === "2" ? "Data analysis and methodology section" : "Presentation slides and delivery practice"}</li>
                  <li><strong>Key steps:</strong> {partNumber === "1" ? "Define research objectives, gather relevant sources, outline structure" : partNumber === "2" ? "Clean dataset, run statistical tests, document methodology" : "Create slides, practice timing, prepare Q&A"}</li>
                  <li><strong>Expected outcome:</strong> {partNumber === "1" ? "Clear research proposal with supporting literature" : partNumber === "2" ? "Comprehensive methodology section with data analysis" : "Polished presentation ready for delivery"}</li>
                  <li><strong>Time estimate:</strong> {partNumber === "1" ? "2-3 hours" : partNumber === "2" ? "3-4 hours" : "1-2 hours"} of focused work</li>
                </ul>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Tips for success:</div>
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  <li>Start by reviewing the specific assignment requirements</li>
                  <li>Break the work into 30-45 minute focused sessions</li>
                  <li>Take short breaks between sessions to maintain focus</li>
                  <li>Save your work frequently and document your progress</li>
                </ul>
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      } else if (userInput.toLowerCase().includes('hello') || userInput.toLowerCase().includes('hi') || userInput.toLowerCase().includes('hey')) {
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                Hello! 👋 I'm your AI Learning Coach.
              </div>
              <div style={{ lineHeight: 1.6 }}>
                I'm here to help you with your study plan, answer questions about your assignments, 
                provide practice exercises, and offer encouragement when you need it!
                <br /><br />
                How can I assist you with your learning today?
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      } else {
        aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>
                I'd love to help you with that! 🤔
              </div>
              <div style={{ lineHeight: 1.6 }}>
                To give you the best assistance, could you tell me a bit more about what you're working on?
                <br /><br />
                You can ask me about:
                <ul style={{ paddingLeft: 18, margin: '8px 0' }}>
                  <li>Your study plan and schedule</li>
                  <li>Specific tasks or assignments</li>
                  <li>Practice exercises for difficult topics</li>
                  <li>Or just ask for some encouragement!</li>
                </ul>
              </div>
            </div>
          ),
          timestamp: new Date()
        };
      }
      
      setChatMessages(prev => [...prev, aiResponse])
    }, 1000)
  }

  const handleSuggestionClick = (suggestion: string) => {
    // 进入聊天态
    setShowChat(true)

    // 根据不同的suggestion设置对应的输入内容
    let inputText = '';
    
    if (suggestion === 'Practice my weak topics') {
      inputText = 'I really couldn’t understand how to xxx and xxx is so hard for me. I want to do a practice of this part.';
    } else if (suggestion === 'Give me some encouragement') {
      inputText = 'Give me some encouragement.';
    } else if (suggestion === 'How to do for Part N of Task X') {
      inputText = 'How should I approach Part 2 of Task "Final Project Report"?';
    } else {
      // 默认：Explain my plan
      inputText = 'Please explain my plan for me.';
    }
    
    // 将文字填入输入框
    setCurrentInput(inputText);
  }

  // 新消息出现时自动滚动到底部
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [chatMessages])

  return (
    <>
      <div className="chat-layout">
        <aside className="sh-sidebar">
          {/* 用户卡 */}
          <div className="sh-profile-card" onClick={() => (window.location.hash = '#/student-profile')} role="button" aria-label="Open profile" style={{cursor:'pointer'}}>
            <div className="avatar"><img
              src={user?.avatarUrl || AvatarIcon}
              width={48}
              height={48}
              alt="avatar"
              style={{ borderRadius: '50%', objectFit: 'cover' }}
              onError={(e) => { (e.currentTarget as HTMLImageElement).src = AvatarIcon; }}
            /></div>
            <div className="info">
              <div className="name">{user?.name ?? ''}</div>
              <div className="studentId">{user?.studentId ?? ''}</div>
            </div>
            <button className="chevron" aria-label="Profile">
              <img src={ArrowRight} width={16} height={16} alt="" />
            </button>
          </div>

          {/* 导航 */}
          <nav className="sh-nav">
            <a className="item" href="#/student-home">
              <img src={IconHome} className="nav-icon" alt="" /> Home
            </a>
            <a className="item" href="#/student-courses">
              <img src={IconCourses} className="nav-icon" alt="" /> My Courses
            </a>
            <a className="item" href="#/student-plan">
              <img src={IconSettings} className="nav-icon" alt="" /> My plan
            </a>
          </nav>

          {/* AI 卡：加入建议按钮 */}
          <div className="sh-ai-card">


            <div className="ai-center-icon">
              <img src="/src/assets/images/ai-svgrepo-com.png" width={128} height={128} alt="AI" style={{opacity: 0.8}} />
            </div>


            <div className="ai-suggestions">
              <div className="ai-s-header">Suggestions for You</div>
              <button className="ai-s-btn" onClick={() => handleSuggestionClick('Explain my plan')} aria-label="Explain my plan">
                <span className="ai-s-label">Explain my plan</span>
                <img className="ai-s-chev" src={ArrowRight} width={16} height={16} alt="" />
              </button>
              <button className="ai-s-btn" onClick={() => handleSuggestionClick('Practice my weak topics')} aria-label="Practice my weak topics">
                <span className="ai-s-label">Practice my weak topics</span>
                <img className="ai-s-chev" src={ArrowRight} width={16} height={16} alt="" />
              </button>
              <button className="ai-s-btn" onClick={() => handleSuggestionClick('How to do for Part N of Task X')} aria-label="How to do for Part N of Task X">
                <span className="ai-s-label">How to do for Part N of Task X</span>
                <img className="ai-s-chev" src={ArrowRight} width={16} height={16} alt="" />
              </button>
              <button className="ai-s-btn" onClick={() => handleSuggestionClick('Give me some encouragement')} aria-label="Give me some encouragement">
                <span className="ai-s-label">Give me some encouragement</span>
                <img className="ai-s-chev" src={ArrowRight} width={16} height={16} alt="" />
              </button>

            </div>


          </div>

          <button className="btn-outline" onClick={handleLogout}>Log Out</button>
        </aside>

        {/* 右侧主区域 */}
        <main className="cw-main">
          <div className="cw-top">
            <button className="cw-back" onClick={goBack} aria-label="Back">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 14L5 8L11 2" stroke="#161616" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div className="cw-title">AI Coach</div>
          </div>

          <section className={`cw-area ${showChat ? 'is-chatting' : ''}`}>
            {/* 顶部装饰与标题：始终展示 */}
            <div className="cw-sparkles" aria-hidden>✦✦</div>
            <h2 className="cw-sub">Your personal learning coach</h2>

            {/* 聊天消息区域：在标题下方显示 */}
            {showChat && (
              <div className="cw-chat-container" aria-live="polite">
                <div className="cw-chat-messages" ref={messagesRef}>
                  {chatMessages.map((message) => (
                    <div key={message.id} className={`cw-message ${message.type}`}>
                      <div className="cw-message-avatar">
                        {message.type === 'ai' ? '🤖' : '👤'}
                      </div>
                      <div className="cw-message-content">
                        <div className="cw-message-label">{message.type === 'ai' ? 'COACH' : 'ME'}</div>
                        <div className="cw-message-text">{message.content}</div>
                        <div className="cw-message-time">
                          {message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 底部输入栏：无论是否开始聊天都保持相同的大小与位置 */}
            <form className="cw-input-row" onSubmit={onSend}>
              <input
                className="cw-input"
                placeholder="Ask me anything about your projects"
                aria-label="Message to AI Coach"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
              />
              <button className="cw-send" type="submit" aria-label="Send">
                ➤
              </button>
            </form>
          </section>
        </main>
      </div>

      {practiceOpen && (
        <div role="dialog" aria-modal="true" aria-label="Practice window"
             style={{position:'fixed', inset:0, background:'rgba(248, 230, 218, 0.35)', backdropFilter:'blur(8px)', WebkitBackdropFilter:'blur(8px)', display:'grid', placeItems:'center', zIndex:1000}}>
          <div style={{position:'relative', width:'min(720px, 92vw)', background:'#fff', borderRadius:26, padding:'26px 26px 22px', boxShadow:'0 18px 44px rgba(0,0,0,0.16)', border:'1px solid #eceff3', textAlign:'center'}}>
            {/* Close button - match Notifications design */}
            <button
              className="close-btn practice-close"
              onClick={() => setPracticeOpen(false)}
              aria-label="close"
              type="button"
            >
              ×
            </button>
            {practiceStage === 'intro' ? (
              <>
                <div style={{fontSize:22, fontWeight:800, color:'#172239', marginTop:4, marginBottom:6, display:'inline-flex', alignItems:'center', gap:8}}>
                  <span>Start Practice</span>
                  <svg width="28" height="28" viewBox="0 0 64 64" fill="none" aria-hidden>
                    <rect x="8" y="12" width="48" height="32" rx="8" stroke="#172239" strokeWidth="3"/>
                    <path d="M32 54l-8-10h16l-8 10z" stroke="#172239" strokeWidth="3" fill="none"/>
                  </svg>
                </div>
                <div style={{color:'#6D6D78', fontSize:14, marginBottom:18}}>This is a 10-minute focused practice for your weak topics.</div>
                <div style={{display:'flex', gap:12, justifyContent:'center'}}>
                  <button
                    aria-label="Start"
                    onClick={() => { setPracticeStage('quiz'); setQuizIndex(0) }}
                    style={{padding:'14px 24px', minWidth:'132px', borderRadius:18, border:'1px solid #FFB790', background:'linear-gradient(180deg,#FFF9F5 0%, #FFEBDD 100%)', boxShadow:'0 8px 18px rgba(255,168,122,0.25)', fontWeight:800, fontSize:16, color:'#172239', cursor:'pointer'}}
                  >
                    Start
                  </button>
                  
                </div>
              </>
            ) : (
              <div style={{textAlign:'left'}}>
                <div style={{marginBottom:12}}>
                  <div style={{fontSize:18, fontWeight:800, color:'#172239', lineHeight:1.4, wordBreak:'break-word', overflowWrap:'anywhere', whiteSpace:'normal'}}>
                    {quizQuestions[quizIndex].q}
                  </div>
                </div>
                
                {quizQuestions[quizIndex].type === 'multiple-choice' ? (
                  <div style={{display:'grid', gap:12, margin:'14px 0 18px'}}>
                    {['A','B','C','D'].map((label, i) => {
                      const isSelected = answers[quizIndex] === i
                      return (
                        <button
                          key={label}
                          onClick={() => { const next = [...answers]; next[quizIndex] = i; setAnswers(next) }}
                          style={{
                            display:'grid', gridTemplateColumns:'36px 1fr', alignItems:'center',
                            padding:'14px 16px', borderRadius:14,
                            border: isSelected ? '2px solid #FF9A6A' : '1px solid #e7e9ef',
                            background: isSelected ? 'linear-gradient(180deg,#FFF9F5 0%, #FFEBDD 100%)' : '#fff',
                            boxShadow: isSelected ? '0 6px 14px rgba(255,168,122,0.18)' : '0 2px 8px rgba(0,0,0,0.06)'
                          }}
                          aria-label={`Option ${label}`}
                        >
                          <span style={{fontWeight:700, color:'#172239'}}>{label}.</span>
                          <span style={{color:'#172239'}}>{quizQuestions[quizIndex].options[i]}</span>
                        </button>
                      )
                    })}
                  </div>
                ) : (
                  <div style={{margin:'14px 0 18px'}}>
                    <textarea
                      value={answers[quizIndex] as string || ''}
                      onChange={(e) => { const next = [...answers]; next[quizIndex] = e.target.value; setAnswers(next) }}
                      placeholder={quizQuestions[quizIndex].placeholder}
                      style={{
                        width: '100%',
                        minHeight: '120px',
                        padding: '14px 16px',
                        borderRadius: '14px',
                        border: '1px solid #e7e9ef',
                        background: '#fff',
                        fontSize: '14px',
                        lineHeight: '1.5',
                        resize: 'vertical',
                        fontFamily: 'inherit'
                      }}
                      aria-label="Essay answer"
                    />
                  </div>
                )}
                <div style={{display:'grid', gridTemplateColumns:'1fr auto 1fr', alignItems:'center', gap:12, marginTop:10}}>
                  <button
                    onClick={() => setQuizIndex(idx => Math.max(0, idx - 1))}
                    style={{justifySelf:'start', padding:'12px 22px', minWidth:'132px', borderRadius:18, border:'1px solid #FF9A6A', background:'linear-gradient(180deg,#FFA87A 0%, #FF9F6C 100%)', color:'#fff', fontWeight:800, cursor:'pointer', boxShadow:'0 8px 18px rgba(255,168,122,0.25)'}}
                    aria-label="Previous"
                  >
                    Previous
                  </button>
                  <div style={{justifySelf:'center', fontSize:13, color:'#8b8f9a'}}>
                    {quizIndex + 1}/{quizQuestions.length}
                  </div>
                  <button
                    onClick={() => {
                      if (quizIndex === quizQuestions.length - 1) {
                        // 计算得分并关闭弹窗，然后在聊天窗口里连续追加两条 COACH 消息
                        const total = quizQuestions.filter(q => q.type === 'multiple-choice').length;
                        const score = answers.reduce((acc, ans, idx) => {
                          if (quizQuestions[idx].type === 'multiple-choice') {
                            return acc + (((ans ?? -1) === quizQuestions[idx].correct) ? 1 : 0);
                          }
                          return acc;
                        }, 0);
                        const pct = total > 0 ? Math.round((score / total) * 100) : 0;
                        setPracticeOpen(false);
                        setPracticeStage('intro');
                        setQuizIndex(0);
                        // 确保聊天窗口可见
                        setShowChat(true);
                        const now = Date.now();
                        const fetchingMsg = {
                          id: now,
                          type: 'ai' as const,
                          content: (
                            <div>
                              <div style={{ fontWeight: 700, marginBottom: 6 }}>
                                Got it! I’m fetching your answers and generating explanations (about 10–15s)…
                              </div>
                              <div>You can stay here—I’ll post the summary once it’s ready.</div>
                            </div>
                          ),
                          timestamp: new Date()
                        };
                        const summaryMsg = {
                          id: now + 1,
                          type: 'ai' as const,
                          content: (
                            <div>
                              <div style={{ marginBottom: 6 }}>
                                All set! Score: {score}/{total} ({pct}%)
                              </div>
                              <div style={{ marginBottom: 6 }}>
                                <strong>Strong:</strong> DP basics, overfitting concepts
                              </div>
                              <div style={{ marginBottom: 6 }}>
                                <strong>Needs review:</strong> Cross‑validation, ROC/PR
                              </div>
                              <div>What would you like to do next?</div>
                            </div>
                          ),
                          timestamp: new Date()
                        };
                        setChatMessages(prev => [...prev, fetchingMsg]);
                        setTimeout(() => {
                          setChatMessages(prev => [...prev, summaryMsg]);
                        }, 1200);
                      } else {
                        setQuizIndex(idx => Math.min(quizQuestions.length - 1, idx + 1));
                      }
                    }}
                    style={{justifySelf:'end', padding:'12px 22px', minWidth:'132px', borderRadius:18, border:'1px solid #FF9A6A', background:'linear-gradient(180deg,#FFA87A 0%, #FF9F6C 100%)', color:'#fff', fontWeight:800, cursor:'pointer', boxShadow:'0 8px 18px rgba(255,168,122,0.25)'}}
                    aria-label={quizIndex === quizQuestions.length - 1 ? 'Submit' : 'Next'}
                  >
                    {quizIndex === quizQuestions.length - 1 ? 'Submit' : 'Next'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <ConfirmationModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={confirmLogout}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmText="Confirm"
        cancelText="Cancel"
      />

      <style>{css}</style>
      {/* 覆盖与美化样式：只影响右侧主区域 */}
      <style>{`
        /* 布局与间距优化 */
        .chat-layout{ gap:24px; padding:32px; }
        /* 放大右侧区域：占满主区 */
        .cw-main{ position:relative; max-width: none; margin: 0; width: 100%; display:flex; flex-direction:column; min-height: calc(100vh - 64px); }

        /* 顶部行：Back更靠近中轴，标题保持右侧 */
        .cw-top{ position:absolute; top:30px; left:36px; right:24px; display:flex; align-items:center; justify-content:space-between; padding:0; z-index:10; }
        /* Back 按钮尺寸对齐 Reschedule：48px 高、16圆角、轻阴影、粗体 */
        /* Back 按钮对齐 StudentProfile 的 icon-btn 样式 */
        .cw-back{
          width:auto; height:auto; padding:13px; /* enlarge hit area without visual change */
          border:none; background:transparent;
          display:flex; align-items:center; justify-content:center;
          box-shadow:none; cursor:pointer;
        }
        /* keep arrow visually in the same place */
        .cw-back svg{ pointer-events:none; margin-left:-12px; margin-top:-12px; }
        .cw-back:hover{ background:#f9fafb }
        .cw-title{ font-size:22px; }

        /* 渐变容器：更柔和的桃色，适度增高，居中并限制最大宽度 */
        /* 渐变容器：加宽并用视口高度计算，保证底边与左侧 Log Out 底边对齐
           计算：页面上下 padding 28*2 = 56，加上顶部行预留 ~64，总高度=100vh-120
        */
        .cw-area{
          max-width: none;
          margin: 0;
          flex: 1;
          padding: 96px 24px 24px; /* 再下移整体内容 */
          border-radius: 28px;
          /* 自下往上递减，顶部更白 */
          background: linear-gradient(to top,rgb(244, 176, 139) 28%, #F8E6DA 62%, #FFFFFF 100%);
          box-shadow: 0 10px 28px rgba(0,0,0,0.06);
          min-height: auto;
          z-index: 1;
          display:flex; flex-direction:column; align-items:center; justify-content:flex-start;
        }
        .cw-sparkles{ font-size: 22px; letter-spacing: 2px; margin-top: 220px; }
        .cw-sub{ font-size: 22px; font-weight: 700; color:#172239; margin-top: 3px; }

        /* 输入区：更大更易点，发送按钮圆形悬浮 */
        /* 输入条：一条长输入框，右侧内嵌圆形发送按钮 */
        .cw-input-row{
          position:absolute;
          left: 24px; right: 24px; bottom: 24px;
          display:block;
        }
        .cw-input{
          width:100%;
          height: 50px; font-size: 15px; border-radius: 14px; background:#fff;
          padding-right: 64px; /* 为右侧发送按钮预留空间 */
          box-shadow: inset 0 1px 0 rgba(187, 157, 157, 0.02);
        }
        .cw-input:focus{ outline: none; border-color:#E1E4EA; box-shadow: 0 0 0 4px rgba(255,168,122,0.18); }
        .cw-send{
          position:absolute; right: 6px; bottom: 5px;
          height: 40px; width: 40px; border-radius: 50%;
          background: linear-gradient(180deg,#ffffff, #f7f7f9);
          color:#5b6474; border:1px solid #e7e9ef;
          box-shadow: 0 6px 16px rgba(0,0,0,0.08);
          display:grid; place-items:center;
        }
        .cw-send:hover{ transform: translateY(-1px); background:#fff; }

        /* 聊天界面样式 */
        .cw-chat-container {
          position: absolute;
          left: 24px;
          right: 24px;
          top: 110px;     /* 再上移以与左侧卡片顶部对齐（原 140px） */
          bottom: 96px;   /* 预留底部输入栏空间 */
          display: flex;
          flex-direction: column;
          width: auto;
          max-width: none;
          margin: 0;
        }

        .cw-chat-messages {
          height: 100%;
          overflow-y: auto; /* 内容过多时出现滚动条 */
          overflow-x: hidden; /* 禁止横向滚动，避免长词造成底部滚动条 */
          padding: 8px 12px 12px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          width: 100%;
          /* Firefox 极简滚动条 */
          scrollbar-width: thin;
          scrollbar-color: rgba(23,34,57,0.25) transparent; /* thumb | track */
          /* 避免滚动条出现/隐藏引起内容抖动 */
          scrollbar-gutter: stable;
        }
        /* WebKit 系列（Chrome/Edge/Safari）极简滚动条 */
        .cw-chat-messages::-webkit-scrollbar {
          width: 8px;
        }
        .cw-chat-messages::-webkit-scrollbar-track {
          background: transparent;
          margin: 6px 0; /* 上下留白，让拇指不贴边 */
        }
        .cw-chat-messages::-webkit-scrollbar-thumb {
          background-color: rgba(23,34,57,0.25);
          border-radius: 999px;
          border: 2px solid transparent; /* 内凹观感，贴边更柔和 */
          background-clip: padding-box;
        }
        .cw-chat-messages:hover::-webkit-scrollbar-thumb {
          background-color: rgba(23,34,57,0.35);
        }
        .cw-chat-messages::-webkit-scrollbar-thumb:active {
          background-color: rgba(23,34,57,0.45);
        }
        .cw-chat-messages::-webkit-scrollbar-corner { background: transparent; }

        .cw-message {
          display: flex;
          gap: 12px;
          align-items: flex-start;
          max-width: 80%;
        }
        .cw-message .cw-message-content{ max-width: 560px; }

        .cw-message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .cw-message.ai {
          align-self: flex-start;
        }

        .cw-message-avatar {
          width: 36px;   /* 头像大小调整为36px */
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px; /* 符号大小相应调整 */
          background: #f0f2f6;
          flex-shrink: 0;
        }

        .cw-message.user .cw-message-avatar {
          background: #ffa87a;
        }

        .cw-message-content {
          background: #fff;
          padding: 14px 16px;
          border-radius: 18px;
          box-shadow: 0 8px 20px rgba(0,0,0,0.08);
          border: 1px solid #eceff3; /* AI 气泡轻描边 */
        }
        .cw-message-label{
          font-size: 12px; /* 放大标签 COACH/ME */
          font-weight: 700;
          letter-spacing: 0.08em;
          color: #8b8f9a;
          margin-bottom: 6px;
        }

        .cw-message.user .cw-message-content {
          /* 更有层次的渐变，略微提升对比 */
          background: linear-gradient(180deg, #FFB790 0%, #FF9F6C 100%);
          color: #fff;
          /* 新增：轻描边 + 内侧高光，避免与背景融在一起 */
          border: 1px solid rgba(210, 118, 80, 0.25);
          background-clip: padding-box;
          /* 外阴影加强，辅以一圈极浅的描边阴影，提升边界清晰度 */
          box-shadow:
            0 10px 22px rgba(255,160,111,0.28),
            0 0 0 1px rgba(160, 80, 45, 0.10);
        }

        .cw-message-text {
          font-size: 14px;       /* 正文字体调整为15px */
          line-height: 1.6;
          margin-bottom: 6px;
          /* 长连续英文自动换行，避免出现底部滚动条 */
          overflow-wrap: anywhere;
          word-break: break-word;
          white-space: normal;
          hyphens: auto;
        }

        .cw-message-time {
          font-size: 11px;
          opacity: 0.6;
        }

        /* 聊天气泡内的 CTA 按钮（如：Start practice） */
        .cw-cta-btn{
          margin-top: 10px;
          padding: 10px 14px;
          border-radius: 14px;
          border: 1px solid #e7e9ef;
          background: #ffffff;
          color: #172239;
          font-weight: 700;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.06);
          cursor: pointer;
        }
        .cw-cta-btn:hover{
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(0,0,0,0.10);
        }
        .cw-cta-btn:active{
          transform: translateY(0);
          box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        }

        .cw-chat-input-row {
          display: flex;
          gap: 12px;
          padding: 20px;
          background: #fff;
          border-top: 1px solid #eaeaea;
        }

        .cw-chat-input {
          flex: 1;
          height: 44px;
          border: 1px solid #eaeaea;
          border-radius: 22px;
          padding: 0 16px;
          font-size: 14px;
        }

        .cw-chat-input:focus {
          outline: none;
          border-color: #ffa87a;
        }

        .cw-chat-send {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          border: none;
          background: #ffa87a;
          color: white;
          font-size: 16px;
          cursor: pointer;
        }

        .cw-chat-send:hover {
          background: #ff9a6a;
        }

        /* 大屏进一步拉伸渐变容器高度 */
        @media (min-width: 1440px){
          .cw-area{ min-height: 680px; padding-top: 110px; }
          .cw-sub{ font-size: 24px; }
        }
        /* 窄屏优化 */
        @media (max-width: 1200px){
          .cw-main{ max-width: 900px; }
          .cw-area{ min-height: 520px; }
        }
        @media (max-width: 920px){
          .cw-main{ max-width: 760px; }
          .cw-area{ min-height: 480px; padding: 72px 20px 20px; }
          .cw-input-row{ left:20px; right:20px; }
        }
      `}</style>
      {/* Practice modal close button style aligned with Notifications */}
      <style>{`
        .practice-close{
          position:absolute; top:10px; right:12px;
        }
        /* Visuals similar to MessageModal .close-btn */
        .practice-close.close-btn{
          width:32px; height:32px; line-height:32px;
          border-radius:8px;
          background: transparent;
          border: none;
          color:#6D6D78;
          font-size:22px;
          display:flex; align-items:center; justify-content:center;
          cursor:pointer;
          transition: background .2s ease;
        }
        .practice-close.close-btn:hover{
          background:#F7F7F8;
        }
        .practice-close.close-btn:focus{
          outline:none;
          box-shadow:0 0 0 2px rgba(255,168,122,0.25);
        }
      `}</style>
    </>
  )
}

const css = `
:root{
  --sh-border: #EAEAEA;
  --sh-muted: #6D6D78;
  --sh-text: #172239;
  --card-bg: #FFFFFF;
  --shadow: 0 8px 24px rgba(0,0,0,0.04);
  --sh-shadow: 0 8px 24px rgba(0,0,0,0.04);
  --sh-blue: #4A90E2;
  --peach-1: #FDEAE0;
  --peach-2: #F8C7AA;
}

.chat-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:24px;
  padding:32px;
  color:var(--sh-text);
  background:#fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height:100vh;
}

/* 侧栏：直接复用 StudentHome 的样式命名以保持一致 */
.sh-sidebar{display:flex;flex-direction:column;gap:24px;height:100%}
.sh-profile-card{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-profile-card .avatar{width:48px;height:48px;border-radius:50%;overflow:hidden;background:#F4F6FA;display:grid;place-items:center;border:1px solid var(--sh-border)}
.sh-profile-card .info .name{font-size:14px;font-weight:700}
.sh-profile-card .chevron{margin-left:auto;background:#fff;border:1px solid var(--sh-border);border-radius:999px;width:36px;height:36px;display:grid;place-items:center}
.sh-nav{display:flex;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow)}
.sh-nav .item{display:flex;align-items:center;gap:16px;padding:14px 16px;border-radius:12px;color:var(--sh-muted);text-decoration:none;font-weight:500}
.sh-nav .item.active{background:#FFA87A;color:#172239;font-weight:800;border-radius:20px}
.sh-nav .nav-icon{width:20px;height:20px}
.sh-ai-card{padding:18px;border:1px solid var(--sh-border);border-radius:20px;background:#fff;box-shadow:var(--sh-shadow);display:flex;flex-direction:column;align-items:center;text-align:center;gap:16px;flex:1;min-height:240px}
.sh-ai-card .ai-title{font-weight:800;font-size:18px}
.sh-ai-card .ai-sub{color:var(--sh-muted);font-size:14px}
.ai-center-icon{margin:16px 0;display:flex;justify-content:center;align-items:center}
.sh-ai-card .ai-icon{width:56px;height:56px;border-radius:14px;background:var(--sh-blue);display:grid;place-items:center}
/* 建议按钮块仅在 ChatWindow 使用 */
.ai-suggestions{width:100%;display:flex;flex-direction:column;gap:10px;align-items:center;margin-top:12px;margin-bottom:0}
.ai-suggestions .ai-s-header{font-weight:800;font-size:19px;margin:6px 0 10px;color:#172239;text-align:center}
.ai-s-btn{
  width:100%;
  height:52px;
  padding:0 16px;
  border:1px solid #FFA87A;
  border-radius:16px;
  background:linear-gradient(180deg,#FFF9F5,#FFF3E9);
  color:#172239;
  font-weight:700;
  font-size:15px;
  cursor:pointer;
  box-shadow:0 3px 12px rgba(255,168,122,0.15);
  transition:all .15s ease;
  display:flex; align-items:center; justify-content:space-between;
}
.ai-s-label{flex:1; text-align:center}
.ai-s-chev{opacity:.8; transition:transform .15s ease; filter: invert(46%) sepia(64%) saturate(500%) hue-rotate(340deg) brightness(100%) contrast(95%);}
.ai-s-btn:hover{
  background:linear-gradient(180deg,#FFF3E9,#FFEBDD);
  box-shadow:0 6px 16px rgba(255,168,122,0.25);
  transform:translateY(-1px);
  border-color:#FF9A6A;
}
.ai-s-btn:hover .ai-s-chev{ transform: translateX(2px); }
.ai-s-btn:active{transform:translateY(0);box-shadow:0 2px 8px rgba(255,168,122,0.12)}
.ai-s-btn:last-child{margin-bottom:0}
.ai-s-btn:focus{outline:none; box-shadow:0 0 0 4px rgba(255,168,122,0.3)}
.ai-s-btn:active{transform:translateY(0);box-shadow:0 2px 8px rgba(255,168,122,0.12)}
.btn-primary.ghost{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:20px 36px;border-radius:24px;background:#F6B48E;color:#172239;border:none;font-weight:800;font-size:16px;width:100%;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.06);transition:all .2s ease}
.btn-primary.ghost:hover{background:#FFA87A;transform:translateY(-1px)}
.btn-primary.ghost.ai-start{padding:20px 20px}
.btn-primary.ghost .label{flex:1;text-align:center}
.btn-primary.ghost.ai-start .spc{width:16px;height:16px;visibility:hidden}
.btn-primary.ghost.ai-start .chev{width:16px;height:16px}
.btn-outline{padding:14px;border-radius:14px;background:#fff;border:1px solid var(--sh-border);cursor:pointer;font-weight:600;margin-top:auto}

/* 右侧主区域 */
.cw-main{display:flex;flex-direction:column;gap:24px}
.cw-top{display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center}
.cw-back{
  justify-self:center;
  padding:10px 18px;border:1px solid var(--sh-border);border-radius:14px;background:#fff;cursor:pointer;font-weight:700;color:#172239;
}
.cw-title{
  justify-self:end;
  font-weight:800;color:#172239;
}

/* 中间渐变容器 */
.cw-area{
  position:relative;
  display:flex;flex-direction:column;align-items:center;
  gap:24px;
  padding:80px 24px 24px;
  border:1px solid var(--sh-border);
  border-radius:28px;
  background: radial-gradient(120% 120% at 50% 10%, #FFF 0%, var(--peach-1) 40%, #fff 100%);
  box-shadow: var(--shadow);
  min-height: 520px;
}
.cw-sparkles{font-size:22px;color:#172239;opacity:.9;margin-top:-24px}
.cw-sub{font-size:20px;font-weight:600;color:#172239;margin:0}
.cw-area.is-chatting .cw-sparkles,
.cw-area.is-chatting .cw-sub{
  opacity:.18;           /* 降低存在感 */
  filter: blur(0.6px);   /* 轻微虚化 */
  transition: opacity .25s ease, filter .25s ease;
  pointer-events: none;  /* 防止误点 */
}

/* 底部输入行 */
.cw-input-row{
  position:absolute;bottom:18px;left:24px;right:24px;
  display:grid;grid-template-columns:1fr 48px;gap:10px;
}
.cw-input{
  height:44px;border-radius:12px;border:1px solid var(--sh-border);padding:0 14px;font-size:14px;color:#172239;background:#fff;
}
.cw-input::placeholder{color:#9aa0a6}
.cw-send{
  height:44px;border-radius:12px;border:1px solid var(--sh-border);background:#fff;cursor:pointer;font-size:18px;color:#6D6D78;
}
@media (max-width: 1200px){
  .chat-layout{grid-template-columns:240px 1fr}
}
`