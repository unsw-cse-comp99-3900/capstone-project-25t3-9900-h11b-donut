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
  // If it is a practice ready message, directly render the practice button
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
                console.log('🎯 practice button being clicked:', practiceInfo);
            
                if ((window as any).openPracticeModal) {
                  (window as any).openPracticeModal(practiceInfo.course, practiceInfo.topic, practiceInfo.sessionId);
                } else {
        
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

  // Analyze message content and extract button

  const parseContent = (text: string) => {
    // Detecting regular expressions for exercise buttons - supports multiple parameter formats

    const buttonRegex = /<button[^>]*class=['"]cw-cta-btn['"][^>]*onclick=['"][^'"]*startPracticeSession\s*(?:&&\s*)?\(\s*([^)]*?)\s*\)['"][^>]*>([\s\S]*?)<\/button>/gi;
    
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = buttonRegex.exec(text)) !== null) {
      // Text before adding button

      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index) || ''
        });
      }

      // Parse Parameters - Supports three parameters: course, topic, and sessionId

      let params = match[1];
      let course = '';
      let topic = '';
      let sessionId = '';
      
      //Compatible as onclick="window.startPracticeSession && window.startPracticeSession('A','B','C')"
      //First, remove the redundancy in the first half and keep the parentheses inside
      params = params.replace(/^.*startPracticeSession\s*\(/, '').replace(/\)\s*$/, '');
      params = params.replace(/['\"]/g, '').trim();
      const paramList = params.split(',').map(p => p.trim()).filter(Boolean);
      
      if (paramList.length >= 3) {
        [course, topic, sessionId] = paramList;
      } else if (paramList.length === 2) {
        [course, topic] = paramList;
      } else if (paramList.length === 1) {
        // A single parameter, which may be a topic or course
        topic = paramList[0];
      }

      console.log('🔍 [ChatMessage] Resolve to button parameters:', { course, topic, sessionId, paramList });

      // Add button information (remove internal HTML tags, only retain plain text tags)

      const buttonLabel = match[2]
        .replace(/<[^>]*>/g, '') // Remove all HTML tags (such as span)
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

    //Add remaining text

    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex) || ''
      });
    }

    // If the button is not found, the entire content is text

    if (parts.length === 0) {
      parts.push({
        type: 'text',
        content: text
      });
    }

    return parts;
  };

  const formatText = (text: string) => {
  //Remove all HTML tags and keep only the text content

    const cleanText = text
      .replace(/<[^>]*>/g, '') 
      .replace(/&nbsp;/g, ' ') 
      .replace(/&lt;/g, '<') 
      .replace(/&gt;/g, '>') 
      .replace(/&amp;/g, '&') 
      .replace(/&quot;/g, '"') 
      .replace(/&#39;/g, "'") 
      .trim();
    
    //Handling line breaks and lists
    return cleanText
      .replace(/\n\s*\n/g, '\n') //Merge multiple line breaks
      .split('\n')
      .filter(line => line.trim() !== '') //Filter empty lines

      .map((line, index) => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('•')) {
          return (
            <div key={index} style={{ marginLeft: '16px', marginBottom: '4px' }}>
              • {trimmedLine.substring(1).trim()}
            </div>
          );
        } else if (/^\d+\.\s/.test(trimmedLine)) {
          //Process numerical lists
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
                    console.log('🔴🔴🔴 button click! 🔴🔴🔴');
                    console.log('📋 button para:', { course: part.course, topic: part.topic, sessionId: part.sessionId });
                    console.log('🔍 window.startPracticeSession type:', typeof (window as any).startPracticeSession);
                    
                    // Call the global startPracticeSession function
                    if ((window as any).startPracticeSession) {
                      console.log('✅ call window.startPracticeSession');
                      (window as any).startPracticeSession(part.course, part.topic, part.sessionId);
                    } else {
                      console.error('❌ window.startPracticeSession undefine!');
                      alert('Practice session function is not available. Please refresh the page.');
                    }
                    // Simultaneously call the incoming callback function (compatibility)

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