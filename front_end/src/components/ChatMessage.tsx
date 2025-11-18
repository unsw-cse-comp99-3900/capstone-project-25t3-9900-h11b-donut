interface ChatMessageProps {
  content: string;
  type: 'user' | 'ai' | 'system';
  timestamp: string;
  onPracticeClick?: (topic: string) => void;
  messageType?: 'practice_ready';
  practiceInfo?: {
    course: string;
    topic: string;
    sessionId: string;
    totalQuestions: number;
  };
}

export function ChatMessageComponent({ content, type, timestamp, onPracticeClick, messageType, practiceInfo }: ChatMessageProps) {
  // 如果是练习就绪消息，直接渲染练习按钮
  if (messageType === 'practice_ready' && practiceInfo) {
    return (
      <div className={`cw-message ${type}`}>
        <div className="cw-message-avatar">
          🤖
        </div>
        <div className="cw-message-content">
          <div className="cw-message-label">COACH</div>
          <div className="cw-message-text">
            <div style={{ marginBottom: '12px' }}>
              {content}
            </div>
            <button
              className="cw-cta-btn"
              onClick={() => {
                console.log('🎯 练习按钮被点击:', practiceInfo);
                // 打开练习弹窗
                if ((window as any).openPracticeModal) {
                  (window as any).openPracticeModal(practiceInfo.course, practiceInfo.topic, practiceInfo.sessionId);
                } else {
                  // 如果没有全局函数，创建一个临时的
                  const event = new CustomEvent('openPractice', {
                    detail: practiceInfo
                  });
                  window.dispatchEvent(event);
                }
              }}
              style={{
                background: 'linear-gradient(180deg, #FFF9F5 0%, #FFEBDD 100%)',
                color: '#FF9F6C',
                border: '1px solid #FFD6B8',
                padding: '12px 20px',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '14px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 2px 8px rgba(255,168,122,0.1)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                marginRight: '8px',
                marginBottom: '8px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.background = 'linear-gradient(180deg, #FFEAD8 0%, #FFDCC8 100%)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(255,168,122,0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.background = 'linear-gradient(180deg, #FFF9F5 0%, #FFEBDD 100%)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(255,168,122,0.1)';
              }}
            >
              Start Practice Session
              <span style={{ marginLeft: '8px' }}>➜</span>
            </button>
          </div>
          <div className="cw-message-time">{timestamp}</div>
        </div>
      </div>
    );
  }

  // 解析消息内容，提取按钮
  const parseContent = (text: string) => {
    // 检测练习按钮的正则表达式 - 支持多种参数格式
    const buttonRegex = /<button[^>]*class=['"]cw-cta-btn['"][^>]*onclick=['"][^'"]*startPracticeSession\s*(?:&&\s*)?\(\s*([^)]*?)\s*\)['"][^>]*>([\s\S]*?)<\/button>/gi;
    
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = buttonRegex.exec(text)) !== null) {
      // 添加按钮前的文本
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index) || ''
        });
      }

      // 解析参数 - 支持三个参数：course, topic, sessionId
      let params = match[1];
      let course = '';
      let topic = '';
      let sessionId = '';
      
      // 兼容形如 onclick="window.startPracticeSession && window.startPracticeSession('A','B','C')"
      // 先去除前半的冗余，保留括号内
      params = params.replace(/^.*startPracticeSession\s*\(/, '').replace(/\)\s*$/, '');
      // 移除成对引号，兼容单双引号和空格
      params = params.replace(/['\"]/g, '').trim();
      const paramList = params.split(',').map(p => p.trim()).filter(Boolean);
      
      if (paramList.length >= 3) {
        [course, topic, sessionId] = paramList;
      } else if (paramList.length === 2) {
        [course, topic] = paramList;
      } else if (paramList.length === 1) {
        // 单个参数，可能是主题或课程
        topic = paramList[0];
      }

      console.log('🔍 [ChatMessage] 解析到按钮参数:', { course, topic, sessionId, paramList });

      // 添加按钮信息（去除内部HTML标签，仅保留纯文本标签）
      const buttonLabel = match[2]
        .replace(/<[^>]*>/g, '') // 去除所有HTML标签（如 span）
        .replace(/→/g, '')
        .replace(/\s+/g, ' ')
        .trim() || 'Start Practice Session';

      parts.push({
        type: 'button',
        course,
        topic,
        sessionId,
        text: buttonLabel
      });

      lastIndex = buttonRegex.lastIndex;
    }

    // 添加剩余的文本
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex) || ''
      });
    }

    // 如果没有找到按钮，整个内容都是文本
    if (parts.length === 0) {
      parts.push({
        type: 'text',
        content: text
      });
    }

    return parts;
  };

  const formatText = (text: string) => {
    // 移除所有HTML标签，只保留文本内容
    const cleanText = text
      .replace(/<[^>]*>/g, '') // 移除所有HTML标签
      .replace(/&nbsp;/g, ' ') // 替换空格实体
      .replace(/&lt;/g, '<') // 替换小于号实体
      .replace(/&gt;/g, '>') // 替换大于号实体
      .replace(/&amp;/g, '&') // 替换和号实体
      .replace(/&quot;/g, '"') // 替换引号实体
      .replace(/&#39;/g, "'") // 替换单引号实体
      .trim();
    
    // 处理换行和列表
    return cleanText
      .replace(/\n\s*\n/g, '\n') // 合并多个换行
      .split('\n')
      .filter(line => line.trim() !== '') // 过滤空行
      .map((line, index) => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('•')) {
          return (
            <div key={index} style={{ marginLeft: '16px', marginBottom: '4px' }}>
              • {trimmedLine.substring(1).trim()}
            </div>
          );
        } else if (/^\d+\.\s/.test(trimmedLine)) {
          // 处理数字列表
          return (
            <div key={index} style={{ marginLeft: '16px', marginBottom: '4px' }}>
              {trimmedLine}
            </div>
          );
        } else {
          return (
            <div key={index} style={{ marginBottom: '4px' }}>
              {trimmedLine}
            </div>
          );
        }
      });
  };

  const parsedParts = parseContent(content);

  return (
    <div className={`cw-message ${type}`}>
      <div className="cw-message-avatar">
        {type === 'ai' ? '🤖' : '👤'}
      </div>
      <div className="cw-message-content">
        <div className="cw-message-label">{type === 'ai' ? 'COACH' : 'ME'}</div>
        <div className="cw-message-text">
          {parsedParts.map((part, index) => {
            if (part.type === 'text') {
              return <div key={index}>{formatText(part.content || '')}</div>;
            } else if (part.type === 'button') {
              return (
                <button
                  key={index}
                  className="cw-practice-button"
                  onClick={() => {
                    console.log('🔴🔴🔴 按钮被点击了! 🔴🔴🔴');
                    console.log('📋 按钮参数:', { course: part.course, topic: part.topic, sessionId: part.sessionId });
                    console.log('🔍 window.startPracticeSession 类型:', typeof (window as any).startPracticeSession);
                    
                    // 调用全局的 startPracticeSession 函数
                    if ((window as any).startPracticeSession) {
                      console.log('✅ 调用 window.startPracticeSession');
                      (window as any).startPracticeSession(part.course, part.topic, part.sessionId);
                    } else {
                      console.error('❌ window.startPracticeSession 未定义!');
                      alert('Practice session function is not available. Please refresh the page.');
                    }
                    // 同时调用传入的回调函数（兼容性）
                    if (onPracticeClick) {
                      onPracticeClick(part.topic || part.course || '');
                    }
                  }}
                  style={{
                    marginTop: '12px',
                    padding: '12px 16px',
                    borderRadius: '16px',
                    border: '1px solid #FFD6B8',
                    background: 'linear-gradient(180deg, #FFF9F5 0%, #FFEBDD 100%)',
                    color: '#FF9F6C',
                    fontWeight: '600',
                    fontSize: '14px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 2px 8px rgba(255,168,122,0.1)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    marginRight: '8px',
                    marginBottom: '8px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.background = 'linear-gradient(180deg, #FFEAD8 0%, #FFDCC8 100%)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(255,168,122,0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.background = 'linear-gradient(180deg, #FFF9F5 0%, #FFEBDD 100%)';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(255,168,122,0.1)';
                  }}
                >
                  {part.text}
                  <span style={{ marginLeft: '8px' }}>➜</span>
                </button>
              );
            }
            return null;
          })}
        </div>
        <div className="cw-message-time">{timestamp}</div>
      </div>
    </div>
  );
}