import { useEffect, useState, useRef } from 'react'
import { ConfirmationModal } from '../../components/ConfirmationModal'
import AvatarIcon from '../../assets/icons/role-icon-64.svg'
import ArrowRight from '../../assets/icons/arrow-right-16.svg'
import IconHome from '../../assets/icons/home-24.svg'
import IconCourses from '../../assets/icons/courses-24.svg'
import IconSettings from '../../assets/icons/settings-24.svg'
import { preferencesStore } from '../../store/preferencesStore'
import { aiChatService, type ChatMessage } from '../../services/aiChatService'

/** ChatWindow
 *  - 左侧：完全复用 StudentHome 的侧栏结构（用户卡/导航/AI卡/登出按钮）
 *  - 右侧：按设计图构建居中内容与输入框
 *  - 仅前端静态样式与交互占位，不接后端（遵循规则：数据走 API，现为占位）
 */
export function ChatWindow() {
  const uid = localStorage.getItem('current_user_id') || ''
  
  // 调试：显示当前用户信息
  console.log('🔍 ChatWindow初始化 - 用户信息:', {
    uid,
    localStorage_current_user_id: localStorage.getItem('current_user_id'),
    auth_token: localStorage.getItem('auth_token') ? 'exists' : 'missing',
    login_time: localStorage.getItem('login_time')
  })
  const [user, setUser] = useState<any>(() => {
    if (!uid) return null
    try { return JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null') }
    catch { return null }
  })
  const [logoutModalOpen, setLogoutModalOpen] = useState(false)
  
  // 聊天状态管理
  const [showChat, setShowChat] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isAiHealthy, setIsAiHealthy] = useState(true)
  const messagesRef = useRef<HTMLDivElement | null>(null)
  const [practiceOpen, setPracticeOpen] = useState(false)
  const [practiceStage, setPracticeStage] = useState<'intro' | 'quiz'>('intro')
  const [showLoadHistory, setShowLoadHistory] = useState(false)
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false) // 标记是否已加载过历史
  
  // 幂等保护ref，防止StrictMode下副作用重复执行
  const initializedRef = useRef(false)

  // 辅助函数：创建默认消息
  const createFallbackMessage = (content: string): ChatMessage => ({
    id: Date.now(),
    type: 'ai',
    content,
    timestamp: new Date().toISOString()
  })

  useEffect(() => {
    if (uid) {
      try { setUser(JSON.parse(localStorage.getItem(`u:${uid}:user`) || 'null')) }
      catch { setUser(null) }
    } else setUser(null)

    // 与 StudentHome 一致：确保周计划预加载（不影响本页 UI）
    preferencesStore.loadWeeklyPlans?.()
  }, [uid])

  // 初始化AI服务和对话状态管理
  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    const initializeAI = async () => {
      console.log('🚀 初始化 AI 聊天窗口', { uid })

      if (!uid) {
        console.log('⚠️ 没有用户ID，跳过初始化')
        return
      }

      const healthy = await aiChatService.healthCheck()
      setIsAiHealthy(healthy)
      if (!healthy) {
        console.log('⚠️ AI 服务不可用')
        return
      }

      // 检查是否是本次登录后第一次进入chat页面
      const loginTime = localStorage.getItem('login_time')
      const chatSessionKey = `chat_visited_${uid}_${loginTime}`
      const hasVisitedChatThisLogin = sessionStorage.getItem(chatSessionKey)
      
      console.log('🔍 检查聊天访问状态:', {
        uid,
        loginTime,
        chatSessionKey,
        hasVisitedChatThisLogin,
        isFirstVisit: !hasVisitedChatThisLogin
      })
      
      if (!hasVisitedChatThisLogin) {
        // 首次进入：隐藏历史，发送问候消息
        console.log('✅ 首次进入chat页面，发送问候消息')
        sessionStorage.setItem(chatSessionKey, 'true')
        
        // 清空之前的聊天消息，确保只显示问候消息
        setChatMessages([])
        setHasLoadedHistory(false)
        setShowLoadHistory(true) // 显示加载历史按钮
        
        console.log('📝 设置初始状态: showLoadHistory=true, hasLoadedHistory=false')
        
        // 防止重复发送问候消息
        setTimeout(async () => {
          // 再次检查是否已经有消息了（防止竞态条件）
          const currentMessages = JSON.parse(sessionStorage.getItem(`chat_state_${uid}`) || '{}').messages || [];
          if (currentMessages.length === 0) {
            await sendWelcomeMessage();
          }
        }, 100);
      } else {
        // 非首次进入：尝试恢复之前的状态
        console.log('🔄 非首次进入，恢复之前的聊天状态')
        const savedState = sessionStorage.getItem(`chat_state_${uid}`)
        console.log('💾 保存的状态:', savedState)
        
        if (savedState) {
          try {
            const { messages, hasLoadedHistory: savedHasLoadedHistory } = JSON.parse(savedState)
            console.log('📋 恢复状态:', { 
              messagesCount: messages?.length || 0, 
              savedHasLoadedHistory,
              willShowLoadHistory: !savedHasLoadedHistory 
            })
            setChatMessages(messages || [])
            setHasLoadedHistory(savedHasLoadedHistory || false)
            setShowLoadHistory(!savedHasLoadedHistory) // 如果还没加载过历史，显示按钮
          } catch (error) {
            console.error('❌ 恢复聊天状态失败:', error)
            // 如果恢复失败，回退到发送问候消息
            setChatMessages([])
            setHasLoadedHistory(false)
            setShowLoadHistory(true)
            await sendWelcomeMessage()
          }
        } else {
          // 没有保存的状态，发送问候消息
          console.log('📝 没有保存的状态，发送问候消息')
          setChatMessages([])
          setHasLoadedHistory(false)
          setShowLoadHistory(true)
          await sendWelcomeMessage()
        }
      }

      setShowChat(true)
    }

    initializeAI()
  }, [uid])

  // 发送欢迎消息的函数（首次进入）
  const sendWelcomeMessage = async () => {
    setIsLoading(true)
    try {
      const response = await aiChatService.sendMessage('welcome')
      if (response.success && response.ai_response) {
        const aiReply: ChatMessage = {
          id: response.ai_response.id,
          type: 'ai',
          content: response.ai_response.content,
          timestamp: response.ai_response.timestamp,
        }
        setChatMessages([aiReply])
      } else {
        setChatMessages([createFallbackMessage('🌟 Hi there! I\'m your AI Learning Coach — great to see you!<br/>How are you feeling today? 😊<br/><br/>I\'m here to help you stay on track and feel confident about your studies.<br/>You can ask me about:<br/>• Your study plan or schedule 🗓️<br/>• Practice exercises for tricky topics 💡<br/>• Or just ask for a little motivation and encouragement! 💬✨<br/><br/>Let\'s make today a productive one! 🚀')])
      }
    } catch (error) {
      console.error('Error sending welcome message:', error)
      setChatMessages([createFallbackMessage('🌟 Hi there! I\'m your AI Learning Coach — great to see you!<br/>How are you feeling today? 😊<br/><br/>I\'m here to help you stay on track and feel confident about your studies.<br/>You can ask me about:<br/>• Your study plan or schedule 🗓️<br/>• Practice exercises for tricky topics 💡<br/>• Or just ask for a little motivation and encouragement! 💬✨<br/><br/>Let\'s make today a productive one! 🚀')])
    } finally {
      setIsLoading(false)
    }
  }

  // 保存聊天状态到sessionStorage
  const saveChatState = () => {
    if (uid) {
      const stateToSave = {
        messages: chatMessages,
        hasLoadedHistory: hasLoadedHistory
      }
      sessionStorage.setItem(`chat_state_${uid}`, JSON.stringify(stateToSave))
      
      // 同时尝试保存到后端数据库（如果后端支持）
      try {
        // 这里可以调用后端API来保存聊天状态
        // 但目前后端可能还没有实现这个功能
        console.log('💾 聊天状态已保存到sessionStorage')
      } catch (error) {
        console.warn('⚠️ 保存到后端失败，但sessionStorage已保存:', error)
      }
    }
  }

  // 格式化消息内容，确保正确的段落和列表格式
  const formatMessageContent = (content: string): string => {
    // 首先清理多余的换行符
    let formatted = content
      .replace(/<br\/?>\s*<br\/?>/gi, '<br/>') // 合并连续的换行符
      .replace(/\n\s*\n/gi, '<br/>') // 合并连续的普通换行符
      .replace(/<br\/?>/gi, '<br/>') // 标准化换行符
      .replace(/\n/g, '<br/>'); // 处理普通换行符
    
    // 处理列表项格式 - 移除原始的•字符，使用CSS添加圆点
    formatted = formatted.replace(/•\s*(.+?)(?=<br|<br\/|$)/g, '<div class="list-item">$1</div>');
    
    return formatted;
  }

  // 当聊天消息或历史加载状态改变时，保存状态
  useEffect(() => {
    if (chatMessages.length > 0) {
      saveChatState()
    }
  }, [chatMessages, hasLoadedHistory, uid])



  const handleLogout = () => {
    setLogoutModalOpen(true)
  }

  const confirmLogout = async () => {
    try {
      // 调用后端 /api/auth/logout
      // await apiService.logout();

      // ✅ 清除所有状态数据
      localStorage.removeItem('auth_token');
      localStorage.removeItem('login_time');
      localStorage.removeItem('current_user_id');
      localStorage.removeItem('ai_chat_session_started');
      
      // 清除所有用户相关的localStorage数据
      if (uid) {
        localStorage.removeItem(`u:${uid}:user`);
        localStorage.removeItem(`u:${uid}:weekly_plans`);
      }
      
      // 清除sessionStorage中的聊天状态
      sessionStorage.clear();

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

  const loadHistoryMessages = async () => {
    console.log('📜 开始加载历史消息')
    const currentUserId = localStorage.getItem('current_user_id')
    console.log('🔍 当前用户ID:', currentUserId)
    console.log('🔍 uid变量:', uid)
    setIsLoading(true)
    try {
      // 不指定days参数，让后端根据消息数量自动决定加载多少天的历史
      const historyResponse = await aiChatService.getChatHistory(200)
      console.log('📡 历史消息响应:', { 
        success: historyResponse.success, 
        messageCount: historyResponse.messages?.length || 0,
        userId: currentUserId
      })
      
      if (historyResponse.success && historyResponse.messages.length > 0) {
        // 获取历史消息并排序
        const historyMessages = historyResponse.messages.sort((a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

        // 合并历史消息和当前会话的消息，允许内容重复（只要不是同一条消息）
        setChatMessages(prev => {
          // 创建消息ID的Set来去重（只去重完全相同的消息ID）
          const existingIds = new Set(prev.map(msg => msg.id));
          const newHistoryMessages = historyMessages.filter(msg => !existingIds.has(msg.id));
          
          // 合并并按时间排序
          const allMessages = [...prev, ...newHistoryMessages].sort((a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
          
          return allMessages;
        });
        
        setHasLoadedHistory(true) // 标记已加载历史
        setShowLoadHistory(false) // 隐藏加载历史按钮
        console.log('✅ 历史消息已合并，保留当前会话消息')
      } else {
        console.log('⚠️ 没有历史消息，隐藏加载按钮')
        setShowLoadHistory(false)
      }
    } catch (error) {
      console.error('❌ 加载历史消息失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 占位题库（前端 mock，不接后端）- 包含选择题和简答题
  const quizQuestions = [
    {
      type: 'multiple-choice' as const,
      q: 'What is the time complexity of binary search?',
      options: ['O(n)', 'O(log n)', 'O(1)', 'O(n^2)'] as const,
      correct: 1
    },
    {
      type: 'multiple-choice' as const,
      q: 'Which data structure is best for FIFO?',
      options: ['Stack', 'Queue', 'Tree', 'Graph'] as const,
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
  ]

  const [quizIndex, setQuizIndex] = useState(0)
  const [answers, setAnswers] = useState<(number | string | null)[]>(Array(quizQuestions.length).fill(null))

  const onSend = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!currentInput.trim() || isLoading || !isAiHealthy) return
    
    const userInput = currentInput.trim()
    setCurrentInput('')
    setIsLoading(true)
    setShowChat(true)
    // 发送消息时不改变Load History按钮状态，保持用户的选择
    
    // 先添加一个临时的用户消息（使用临时ID）
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      content: userInput,
      timestamp: new Date().toISOString()
    }
    
    setChatMessages(prev => [...prev, tempUserMessage])
    
    try {
      // 发送消息到AI服务 - 现在会根据用户的具体内容进行智能回复
      const currentUserId = localStorage.getItem('current_user_id')
      console.log('🚀 发送消息:', { 
        userInput, 
        currentUserId, 
        uid,
        localStorage_keys: Object.keys(localStorage),
        localStorage_current_user_id: localStorage.getItem('current_user_id'),
        all_localStorage: Object.fromEntries(Object.keys(localStorage).map(key => [key, localStorage.getItem(key)]))
      })
      
      // 如果没有用户ID，这是一个严重问题，不应该设置随机ID
      if (!currentUserId) {
        console.error('❌ 严重错误：没有找到用户ID！')
        console.error('localStorage内容:', Object.fromEntries(Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])))
        alert('用户未登录或登录信息丢失，请重新登录')
        window.location.hash = '/login-student'
        return
      }
      
      const response = await aiChatService.sendMessage(userInput)
      
      if (response.success && response.ai_response) {
        // 更新用户消息为后端返回的真实消息，然后添加AI回复
        const realUserMessage: ChatMessage = response.user_message ? {
          id: response.user_message.id,
          type: 'user',
          content: response.user_message.content,
          timestamp: response.user_message.timestamp,
        } : tempUserMessage;
        
        const aiReply: ChatMessage = {
          id: response.ai_response.id,
          type: 'ai',
          content: response.ai_response.content,
          timestamp: response.ai_response.timestamp,
        }
        
        // 替换临时用户消息为真实消息，并添加AI回复
        setChatMessages(prev => {
          const withoutTemp = prev.slice(0, -1); // 移除临时用户消息
          return [...withoutTemp, realUserMessage, aiReply];
        })

        // 如果AI回复包含练习按钮，设置全局函数
        if (response.ai_response.content.includes('Start 10-minute practice session')) {
          (window as any).startPracticeSession = () => {
            setPracticeStage('intro')
            setQuizIndex(0)
            setAnswers(Array(quizQuestions.length).fill(null))
            setPracticeOpen(true)
          }
        }
      } else {
        setChatMessages(prev => [
          ...prev,
          createFallbackMessage(`Sorry, I encountered an error: ${response.error || 'Unknown error'}. Please try again.`)
        ])
      }
      
      // 不再自动同步后端数据，避免覆盖新消息
      // 用户可以通过"Load History"按钮手动加载历史消息
      
    } catch (error) {
      console.error('Error sending message:', error)
      setChatMessages(prev => [
        ...prev,
        createFallbackMessage('Sorry, I\'m having trouble connecting right now. Please try again in a moment.')
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    if (isLoading || !isAiHealthy) return

    let message = ''
    switch (suggestion) {
      case 'Explain my plan':
        message = 'Please explain my plan for me.'
        break
      case 'Practice my weak topics':
        message = 'I really couldn\'t understand some topics and they are so hard for me. I want to do a practice of this part.'
        break
      case 'How to do for Part N of Task X':
        message = 'How should I approach Part 2 of Task "Final Project Report"?'
        break
      case 'Give me some encouragement':
        message = 'Give me some encouragement.'
        break
      default:
        message = suggestion
    }

    setCurrentInput(message)
    setShowChat(true)

    setTimeout(() => {
      const inputElement = document.querySelector('.cw-input') as HTMLInputElement
      inputElement?.focus()
      inputElement?.setSelectionRange(message.length, message.length)
    }, 50)
  }

  // 新消息出现时自动滚动到底部
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [chatMessages])

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

          {/* 加载历史消息按钮 - 放在对话框上方中间 */}
          {showLoadHistory && (
            <div className="cw-load-history-container">
              <button 
                className="cw-load-history-btn"
                onClick={loadHistoryMessages}
                disabled={isLoading}
                aria-label="Load chat history"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 1C4.134 1 1 4.134 1 8s3.134 7 7 7 7-3.134 7-7-3.134-7-7-7zm0 12.5c-3.038 0-5.5-2.462-5.5-5.5S4.962 2.5 8 2.5s5.5 2.462 5.5 5.5-2.462 5.5-5.5 5.5z" fill="currentColor"/>
                  <path d="M8 4v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                {isLoading ? 'Loading...' : 'Load History'}
              </button>
            </div>
          )}

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
                        <div 
                          className="cw-message-text"
                          dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                        />
                        <div className="cw-message-time">
                          {aiChatService.formatTimestamp(message.timestamp)}
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
                placeholder={
                  !isAiHealthy 
                    ? "AI service is currently unavailable..." 
                    : isLoading 
                      ? "Sending message..." 
                      : "Ask me anything about your projects"
                }
                aria-label="Message to AI Coach"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                disabled={isLoading || !isAiHealthy}
              />
              <button 
                className="cw-send" 
                type="submit" 
                aria-label="Send"
                disabled={isLoading || !isAiHealthy || !currentInput.trim()}
              >
                {isLoading ? '⏳' : '➤'}
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
                      const question = quizQuestions[quizIndex]
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
                          <span style={{color:'#172239'}}>{question.type === 'multiple-choice' ? question.options[i] : ''}</span>
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
                        const score = answers.reduce((acc: number, ans, idx) => {
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
                        const fetchingMsg: ChatMessage = {
                          id: now,
                          type: 'ai',
                          content: `Got it! I'm fetching your answers and generating explanations (about 10–15s)…\nYou can stay here—I'll post the summary once it's ready.`,
                          timestamp: new Date().toISOString()
                        };
                        const summaryMsg: ChatMessage = {
                          id: now + 1,
                          type: 'ai',
                          content: `All set! Score: ${score}/${total} (${pct}%)\n\n**Strong:** DP basics, overfitting concepts\n\n**Needs review:** Cross‑validation, ROC/PR\n\nWhat would you like to do next?`,
                          timestamp: new Date().toISOString()
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
        
        /* 消息内容的格式美化 */
        .cw-message-text br {
          display: block;
          margin-bottom: 6px; /* 减小段落间距 */
        }
        
        .cw-message-text br + br {
          margin-bottom: 0; /* 连续两个换行只保留一个间距 */
        }
        
        /* 列表项的美化 */
        .cw-message-text .list-item {
          display: block;
          margin: 4px 0;
          padding-left: 16px;
          position: relative;
          line-height: 1.5;
        }
        
        .cw-message-text .list-item:before {
          content: "•";
          position: absolute;
          left: 4px;
          color: #ffa87a;
          font-weight: bold;
          font-size: 14px;
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

        /* 加载历史消息按钮样式 */
        .cw-load-history-container {
          position: absolute;
          top: 80px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 20;
        }
        
        .cw-load-history-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          border: 1px solid #e7e9ef;
          border-radius: 14px;
          background: #fff;
          color: #6D6D78;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.08);
          transition: all 0.2s ease;
          min-width: 140px;
          justify-content: center;
        }
        
        .cw-load-history-btn:hover:not(:disabled) {
          background: #f9fafb;
          border-color: #d1d5db;
          transform: translateX(-50%) translateY(-1px);
          box-shadow: 0 6px 16px rgba(0,0,0,0.12);
        }
        
        .cw-load-history-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .cw-load-history-btn:active:not(:disabled) {
          transform: translateX(-50%) translateY(0);
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
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
          .cw-history-dropdown { right: 20px; }
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
:root {
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

.chat-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  padding: 32px;
  color: var(--sh-text);
  background: #fff;
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  min-height: 100vh;
}

/* 侧栏：直接复用 StudentHome 的样式命名以保持一致 */
.sh-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
}

.sh-profile-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--sh-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--sh-shadow);
}

.sh-profile-card .avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: #F4F6FA;
  display: grid;
  place-items: center;
  border: 1px solid var(--sh-border);
}

.sh-profile-card .info .name {
  font-size: 14px;
  font-weight: 700;
}

.sh-profile-card .chevron {
  margin-left: auto;
  background: #fff;
  border: 1px solid var(--sh-border);
  border-radius: 999px;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
}

.sh-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--sh-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--sh-shadow);
}

.sh-nav .item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  color: var(--sh-muted);
  text-decoration: none;
  font-weight: 500;
}

.sh-nav .item.active {
  background: #FFA87A;
  color: #172239;
  font-weight: 800;
  border-radius: 20px;
}

.sh-nav .nav-icon {
  width: 20px;
  height: 20px;
}

.sh-ai-card {
  padding: 18px;
  border: 1px solid var(--sh-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--sh-shadow);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
  flex: 1;
  min-height: 240px;
}

.sh-ai-card .ai-title {
  font-weight: 800;
  font-size: 18px;
}

.sh-ai-card .ai-sub {
  color: var(--sh-muted);
  font-size: 14px;
}

.ai-center-icon {
  margin: 16px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.sh-ai-card .ai-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--sh-blue);
  display: grid;
  place-items: center;
}

/* 建议按钮块仅在 ChatWindow 使用 */
.ai-suggestions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  margin-bottom: 0;
}

.ai-suggestions .ai-s-header {
  font-weight: 800;
  font-size: 19px;
  margin: 6px 0 10px;
  color: #172239;
  text-align: center;
}

.ai-s-btn {
  width: 100%;
  height: 52px;
  padding: 0 16px;
  border: 1px solid #FFA87A;
  border-radius: 16px;
  background: linear-gradient(180deg, #FFF9F5, #FFF3E9);
  color: #172239;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 3px 12px rgba(255,168,122,0.15);
  transition: all .15s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-s-label {
  flex: 1;
  text-align: center;
}

.ai-s-chev {
  opacity: .8;
  transition: transform .15s ease;
  filter: invert(46%) sepia(64%) saturate(500%) hue-rotate(340deg) brightness(100%) contrast(95%);
}

.ai-s-btn:hover {
  background: linear-gradient(180deg, #FFF3E9, #FFEBDD);
  box-shadow: 0 6px 16px rgba(255,168,122,0.25);
  transform: translateY(-1px);
  border-color: #FF9A6A;
}

.ai-s-btn:hover .ai-s-chev {
  transform: translateX(2px);
}

.ai-s-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(255,168,122,0.12);
}

.ai-s-btn:last-child {
  margin-bottom: 0;
}

.ai-s-btn:focus {
  outline: none;
  box-shadow: 0 0 0 4px rgba(255,168,122,0.3);
}

.btn-primary.ghost {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 20px 36px;
  border-radius: 24px;
  background: #F6B48E;
  color: #172239;
  border: none;
  font-weight: 800;
  font-size: 16px;
  width: 100%;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
  transition: all .2s ease;
}

.btn-primary.ghost:hover {
  background: #FFA87A;
  transform: translateY(-1px);
}

.btn-primary.ghost.ai-start {
  padding: 20px 20px;
}

.btn-primary.ghost .label {
  flex: 1;
  text-align: center;
}

.btn-primary.ghost.ai-start .spc {
  width: 16px;
  height: 16px;
  visibility: hidden;
}

.btn-primary.ghost.ai-start .chev {
  width: 16px;
  height: 16px;
}

.btn-outline {
  padding: 14px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--sh-border);
  cursor: pointer;
  font-weight: 600;
  margin-top: auto;
}

/* 右侧主区域 */
.cw-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.cw-top {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  align-items: center;
}

.cw-back {
  justify-self: center;
  padding: 10px 18px;
  border: 1px solid var(--sh-border);
  border-radius: 14px;
  background: #fff;
  cursor: pointer;
  font-weight: 700;
  color: #172239;
}

.cw-title {
  justify-self: end;
  font-weight: 800;
  color: #172239;
}

/* 中间渐变容器 */
.cw-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 80px 24px 24px;
  border: 1px solid var(--sh-border);
  border-radius: 28px;
  background: radial-gradient(120% 120% at 50% 10%, #FFF 0%, var(--peach-1) 40%, #fff 100%);
  box-shadow: var(--shadow);
  min-height: 520px;
}

.cw-sparkles {
  font-size: 22px;
  color: #172239;
  opacity: .9;
  margin-top: -24px;
}

.cw-sub {
  font-size: 20px;
  font-weight: 600;
  color: #172239;
  margin: 0;
}

.cw-area.is-chatting .cw-sparkles,
.cw-area.is-chatting .cw-sub {
  opacity: .18;
  filter: blur(0.6px);
  transition: opacity .25s ease, filter .25s ease;
  pointer-events: none;
}

/* 底部输入行 */
.cw-input-row {
  position: absolute;
  bottom: 18px;
  left: 24px;
  right: 24px;
  display: grid;
  grid-template-columns: 1fr 48px;
  gap: 10px;
}

.cw-input {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--sh-border);
  padding: 0 14px;
  font-size: 14px;
  color: #172239;
  background: #fff;
}

.cw-input::placeholder {
  color: #9aa0a6;
}

.cw-send {
  height: 44px;
  border-radius: 12px;
  border: 1px solid var(--sh-border);
  background: #fff;
  cursor: pointer;
  font-size: 18px;
  color: #6D6D78;
}

/* 日期分组样式 */
.cw-message-group {
  margin-bottom: 24px;
}

.cw-date-separator {
  display: flex;
  justify-content: center;
  margin: 20px 0 16px 0;
}

.cw-date-label {
  background: #f0f2f6;
  color: #6D6D78;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (max-width: 1200px) {
  .chat-layout {
    grid-template-columns: 240px 1fr;
  }
}
`