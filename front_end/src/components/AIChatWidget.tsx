/**
 * AI对话组件
 * 可复用的AI对话界面组件
 */
import { useState, useEffect, useRef } from 'react';
import { aiChatService, type ChatMessage } from '../services/aiChatService';

interface AIChatWidgetProps {
  className?: string;
  placeholder?: string;
  maxHeight?: string;
  showHistory?: boolean;
}

export function AIChatWidget({ 
  className = '', 
  placeholder = 'Ask me anything about your projects',
  maxHeight = '400px',
  showHistory = true
}: AIChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);

  // 加载对话历史
  useEffect(() => {
    if (showHistory) {
      loadChatHistory();
    }
  }, [showHistory]);

  // 自动滚动到底部
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const loadChatHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const history = await aiChatService.getChatHistory(50);
      setMessages(history.messages);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (!currentInput.trim() || isLoading) return;

    const userMessage = currentInput.trim();
    setCurrentInput('');
    setIsLoading(true);

    // 立即显示用户消息
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const response = await aiChatService.sendMessage(userMessage);
      
      // 替换临时用户消息并添加AI回复
      setMessages(prev => {
        const newMessages = prev.slice(0, -1); // 移除临时消息
        return [
          ...newMessages,
          response.user_message,
          response.ai_response
        ];
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // 显示错误消息
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatMessageContent = (content: string) => {
    // 简单的markdown格式化
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className={`ai-chat-widget ${className}`}>
      {/* 消息区域 */}
      <div 
        className="chat-messages" 
        ref={messagesRef}
        style={{ maxHeight }}
      >
        {isLoadingHistory && (
          <div className="loading-indicator">
            <div className="loading-text">Loading chat history...</div>
          </div>
        )}
        
        {messages.length === 0 && !isLoadingHistory && (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <div className="empty-title">Hi! I'm your AI Learning Coach</div>
            <div className="empty-subtitle">
              Ask me about your study plan, assignments, or anything else you need help with!
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-avatar">
              {message.type === 'ai' ? '🤖' : '👤'}
            </div>
            <div className="message-content">
              <div className="message-label">
                {message.type === 'ai' ? 'COACH' : 'ME'}
              </div>
              <div 
                className="message-text"
                dangerouslySetInnerHTML={{ 
                  __html: formatMessageContent(message.content) 
                }}
              />
              <div className="message-time">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: '2-digit', 
                  minute: '2-digit'
                })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message ai">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-label">COACH</div>
              <div className="message-text typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <form className="chat-input-form" onSubmit={sendMessage}>
        <input
          className="chat-input"
          placeholder={placeholder}
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          disabled={isLoading}
        />
        <button 
          className="chat-send-btn" 
          type="submit" 
          disabled={!currentInput.trim() || isLoading}
        >
          ➤
        </button>
      </form>

      <style jsx>{`
        .ai-chat-widget {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #fff;
          border-radius: 16px;
          overflow: hidden;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          scrollbar-width: thin;
          scrollbar-color: rgba(0,0,0,0.2) transparent;
        }

        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
          background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
          background-color: rgba(0,0,0,0.2);
          border-radius: 3px;
        }

        .loading-indicator {
          display: flex;
          justify-content: center;
          padding: 20px;
        }

        .loading-text {
          color: #666;
          font-size: 14px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
          text-align: center;
          height: 100%;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .empty-title {
          font-size: 18px;
          font-weight: 700;
          color: #172239;
          margin-bottom: 8px;
        }

        .empty-subtitle {
          font-size: 14px;
          color: #666;
          line-height: 1.5;
        }

        .message {
          display: flex;
          gap: 12px;
          align-items: flex-start;
          max-width: 85%;
        }

        .message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .message.ai {
          align-self: flex-start;
        }

        .message-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          background: #f0f2f6;
          flex-shrink: 0;
        }

        .message.user .message-avatar {
          background: #ffa87a;
        }

        .message-content {
          background: #fff;
          padding: 12px 16px;
          border-radius: 16px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          border: 1px solid #eceff3;
          max-width: 100%;
        }

        .message.user .message-content {
          background: linear-gradient(180deg, #FFB790 0%, #FF9F6C 100%);
          color: #fff;
          border: 1px solid rgba(210, 118, 80, 0.25);
        }

        .message-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: #8b8f9a;
          margin-bottom: 4px;
        }

        .message.user .message-label {
          color: rgba(255,255,255,0.8);
        }

        .message-text {
          font-size: 14px;
          line-height: 1.5;
          margin-bottom: 4px;
          word-wrap: break-word;
        }

        .message-time {
          font-size: 10px;
          opacity: 0.6;
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
          align-items: center;
        }

        .typing-indicator span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #666;
          animation: typing 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }

        .chat-input-form {
          display: flex;
          gap: 8px;
          padding: 16px;
          border-top: 1px solid #eee;
          background: #fff;
        }

        .chat-input {
          flex: 1;
          height: 40px;
          border: 1px solid #ddd;
          border-radius: 20px;
          padding: 0 16px;
          font-size: 14px;
          outline: none;
        }

        .chat-input:focus {
          border-color: #ffa87a;
          box-shadow: 0 0 0 2px rgba(255,168,122,0.2);
        }

        .chat-input:disabled {
          background: #f5f5f5;
          color: #999;
        }

        .chat-send-btn {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: none;
          background: #ffa87a;
          color: white;
          font-size: 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .chat-send-btn:hover:not(:disabled) {
          background: #ff9a6a;
          transform: translateY(-1px);
        }

        .chat-send-btn:disabled {
          background: #ccc;
          cursor: not-allowed;
          transform: none;
        }
      `}</style>
    </div>
  );
}