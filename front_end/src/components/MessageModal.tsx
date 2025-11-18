import { useState, useEffect } from 'react';
import type { Message, MessageType } from '../types/message';
import { MESSAGE_TYPES } from '../types/message';
import apiService from '../services/api';

interface MessageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUnreadCountChange?: (count: number) => void;
}

export function MessageModal({ isOpen, onClose, onUnreadCountChange }: MessageModalProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedType, setSelectedType] = useState<MessageType>('all');

  // 加载消息列表
  const loadMessages = async () => {
    if (!isOpen) return;
    
    setLoading(true);
    try {
      const messages = await apiService.getMessages();
      setMessages(messages);
      const newUnreadCount = messages.filter(msg => !msg.isRead).length;
      setUnreadCount(newUnreadCount);
      onUnreadCountChange?.(newUnreadCount);
    } catch (error) {
      console.error('加载消息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 标记消息为已读
  const markAsRead = async (messageId: string) => {
    try {
      const message = messages.find(msg => msg.id === messageId);
      if (message && !message.isRead) {
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, isRead: true } : msg
        ));
        const newUnreadCount = unreadCount - 1;
        setUnreadCount(newUnreadCount);
        onUnreadCountChange?.(newUnreadCount);
        
        await apiService.markMessageAsRead(messageId);
      }
    } catch (error) {
      console.error('Mark all messages as read failed with one click:', error);
    }
  };

  // 一键标记所有消息为已读
  const markAllAsRead = async () => {
    try {
      const unreadMessages = messages.filter(msg => !msg.isRead);
      if (unreadMessages.length === 0) return;
      
      const unreadMessageIds = unreadMessages.map(msg => msg.id);
      
      setMessages(prev => prev.map(msg => 
        unreadMessageIds.includes(msg.id) ? { ...msg, isRead: true } : msg
      ));
      
      setUnreadCount(0);
      onUnreadCountChange?.(0);
      
      await apiService.markMessagesAsRead(unreadMessageIds);
    } catch (error) {
      console.error('Mark all messages as read failed with one click:', error);
    }
  };

  // 格式化时间显示（英文相对时间）
  const formatTime = (timestamp: string) => {
    const now = new Date();
    const t = new Date(timestamp);
    const diffMs = now.getTime() - t.getTime();
    if (diffMs < 45 * 1000) return 'Now';
    const mins = Math.floor(diffMs / (60 * 1000));
    if (mins < 60) return `${mins} mins ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} hours ago`;
    const days = Math.floor(hours / 24);
    return `${days} days ago`;
  };

  const getMessageIcon = (type: string) => {
  // 所有 due_ 开头的
  if (type.startsWith('due_')) {
    return '⏰';
  }

  // nightly notice
  if (type === 'nightly_notice') {
    return '❗';
  }

  // weekly bonus / bonus / bonus_xxx
  if (type.includes('bonus')) {
    return '🏆';
  }

  // 所有 system_notification 相关
  if (type.startsWith('system')) {
    return '🔔';
  }

  // 默认
  return '📧';
};


  // 筛选消息并按时间倒序排列（最新的在最前面）
  const filteredMessages = messages
    .filter(message =>
      selectedType === 'all' ||

      // ⭐ due_alert 动态类型
      (selectedType === 'due_alert' && message.type.startsWith('due_')) ||

      // ⭐ system_notification 动态类型
      (selectedType === 'system_notification' && message.type.startsWith('system')) ||

      // 原来的严格匹配
      message.type === selectedType
    )
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    // .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());



  // 依据类型生成简洁行文案
  const formatMessage = (m: Message) => {
    if (m.type === 'due_alert') {
      let hoursLeft: number | null = null;
      const anyM: any = m as any;
      if (anyM.dueTime) {
        const due = new Date(anyM.dueTime as string).getTime();
        const now = Date.now();
        hoursLeft = Math.max(0, Math.floor((due - now) / (1000 * 60 * 60)));
      }
      const preview = (anyM.preview || '') as string;
      const match = /"([^"]+)"/.exec(preview);
      const taskName = match ? match[1] : 'Assignment';
      const course = (anyM.courseId || '') as string;
      
      // 检查是否是管理员修改DDL的消息
      if (preview.includes('Admin has') || preview.includes('deadline updated') || preview.includes('deadline changed')) {
        if (preview.includes('extended')) {
          return `Deadline extended: ${taskName} – ${course}`;
        } else if (preview.includes('moved up')) {
          return `Deadline moved up: ${taskName} – ${course}`;
        } else {
          return `Deadline updated: ${taskName} – ${course}`;
        }
      }
      
      const leftText = hoursLeft !== null ? `${hoursLeft}h left` : 'Due soon';
      return `${leftText} for ${taskName} – ${course}`.trim();
    }
    if (m.type === 'nightly_notice') {
      return `Yesterday's plan incomplete. Auto-rescheduled at 00:00.`;
    }
    if (m.type === 'weekly_bonus') {
      return `Nice work! All done on time this week – 0.01 bonus added.`;
    }
    if (m.type === 'system_notification') {
      return m.title || m.preview || 'System notification';
    }
    return m.title || m.preview || '';
  };

  useEffect(() => {
    if (isOpen) {
      loadMessages();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="message-modal-overlay" onClick={onClose}>
      <div className="message-modal" onClick={(e) => e.stopPropagation()}>
        <div className="message-modal-header">
          <div className="header-left">
            <h3 className="message-modal-title">Notifications</h3>
          </div>
          <div className="header-right">
            <button className="close-btn" onClick={onClose} aria-label="close">
              ×
            </button>
          </div>
        </div>

        {/* 消息分类筛选器行 - 包含筛选器、未读计数和All read按钮 */}
        <div className="message-filter-row">
          <div className="filter-dropdown-container">
            <select 
              className="filter-dropdown"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as MessageType)}
            >
              {(Object.entries(MESSAGE_TYPES) as [MessageType, typeof MESSAGE_TYPES[MessageType]][]).map(([type, config]) => (
                <option key={type} value={type}>
                  {config.icon} {config.label}
                </option>
              ))}
            </select>
            <div className="dropdown-arrow">▼</div>
          </div>
          
          <div className="filter-controls">
            {unreadCount > 0 && (
              <span className="unread-badge">{unreadCount} unread</span>
            )}
            {unreadCount > 0 && (
              <button 
                className="mark-all-read-btn"
                onClick={() => markAllAsRead()}
                aria-label="Mark all as read"
              >
                All read
              </button>
            )}
          </div>
        </div>

        <div className="message-modal-content">
          {loading ? (
            <div className="loading">loading...</div>
          ) : messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>No message</p>
            </div>
          ) : (
            <div className="message-list">
              {filteredMessages.length === 0 ? (
                <div className="empty-filter-state">
                  <div className="empty-filter-icon">🔍</div>
                  <p>No {selectedType === 'all' ? 'messages' : MESSAGE_TYPES[selectedType].label.toLowerCase()} found</p>
                  <button 
                    className="reset-filter-btn"
                    onClick={() => setSelectedType('all')}
                  >
                    Show all messages
                  </button>
                </div>
              ) : (
                filteredMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`message-item ${message.isRead ? 'read' : 'unread'}`}
                    onClick={() => markAsRead(message.id)}
                  >
                    <div className="message-icon">
                      {getMessageIcon(message.type)}
                    </div>
                    <div className="message-content">
                      <div className="message-title">{formatMessage(message)}</div>
                    </div>
                    <div className="message-time message-time-right">{formatTime(message.createdAt)}</div>
                    {!message.isRead && <div className="unread-dot"></div>}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <style>{`
        .message-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.2);
          backdrop-filter: saturate(180%) blur(2px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.3s ease-out;
          will-change: transform;
        }

        .message-modal {
          background: #fff;
          border-radius: 18px;
          width: 600px;
          height: 700px;
          display: flex;
          flex-direction: column;
          box-shadow: 0 10px 28px rgba(0,0,0,0.08);
          border: 1px solid #EAEAEA;
          overflow: hidden;
        }

        .message-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid #EAEAEA;
          background: #fff;
          color: #172239;
          position: relative;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .mark-all-read-btn {
          background: #FFA87A;
          color: #172239;
          border: none;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
        }

        .mark-all-read-btn:hover {
          background: #FF8A5C;
          transform: translateY(-1px);
        }

        .message-modal-title {
          margin: 0;
          font-size: 20px;
          font-weight: 800;
          display: flex;
          align-items: center;
          gap: 10px;
          color: #172239;
          letter-spacing: -0.02em;
          /* 居中标题：绝对定位到头部容器中心 */
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
        }

        .message-modal-title::after {
          content: '🔔';
          font-size: 20px;
        }

        .unread-badge {
          background: #FFF3E9;
          color: #FF6B35;
          border-radius: 12px;
          padding: 6px 12px;
          font-size: 14px;
          font-weight: 800;
          letter-spacing: -0.01em;
        }

        .close-btn {
          background: transparent;
          border: none;
          font-size: 22px;
          cursor: pointer;
          color: #6D6D78;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background .2s ease;
        }

        .close-btn:hover {
          background: #F7F7F8;
        }

        .message-modal-content {
          flex: 1;
          overflow-y: auto;
          padding: 8px 12px 16px;
          background: #FAFAFB;
          max-height: calc(700px - 120px);
        }

        .message-modal-content::-webkit-scrollbar {
          width: 6px;
        }

        .message-modal-content::-webkit-scrollbar-track {
          background: rgba(255, 168, 122, 0.1);
          border-radius: 3px;
        }

        .message-modal-content::-webkit-scrollbar-thumb {
          background: rgba(255, 168, 122, 0.4);
          border-radius: 3px;
        }

        .message-modal-content::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 168, 122, 0.6);
        }

        /* 消息分类筛选器行样式 */
        .message-filter-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 20px;
          border-bottom: none;
          background: #FAFAFB;
          gap: 16px;
        }

        .filter-dropdown-container {
          position: relative;
          flex: 1;
          max-width: 200px;
        }

        .filter-dropdown {
          width: 100%;
          padding: 8px 32px 8px 12px;
          border: 1px solid #EAEAEA;
          border-radius: 8px;
          background: #FAFAFB;
          color: #172239;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          appearance: none;
          transition: all 0.2s ease;
        }

        .filter-dropdown:hover {
          border-color: #B8B8C5;
          background: #F0F2F6;
        }

        .filter-dropdown:focus {
          outline: none;
          border-color: #FFA87A;
          box-shadow: 0 0 0 2px rgba(255, 168, 122, 0.2);
        }

        .dropdown-arrow {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: #6D6D78;
          font-size: 12px;
          pointer-events: none;
        }

        .filter-controls {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-shrink: 0;
        }

        .filter-controls .unread-badge {
          background: #FFF3E9;
          color: #FF6B35;
          border-radius: 12px;
          padding: 6px 12px;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: -0.01em;
        }

        .filter-controls .mark-all-read-btn {
          background: #FFA87A;
          color: #172239;
          border: none;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
        }

        .filter-controls .mark-all-read-btn:hover {
          background: #FF8A5C;
          transform: translateY(-1px);
        }

        /* 筛选为空状态 */
        .empty-filter-state {
          padding: 80px 40px;
          text-align: center;
          color: #B8B8C5;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .empty-filter-icon {
          font-size: 48px;
          opacity: 0.6;
        }

        .empty-filter-state p {
          font-size: 16px;
          margin: 0;
          font-weight: 500;
        }

        .reset-filter-btn {
          background: #FFA87A;
          color: #172239;
          border: none;
          border-radius: 8px;
          padding: 8px 16px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-top: 8px;
        }

        .reset-filter-btn:hover {
          background: #FF8A5C;
          transform: translateY(-1px);
        }

        .loading {
          padding: 60px 40px;
          text-align: center;
          color: #FFA87A;
          font-size: 16px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .loading::before {
          content: '⏳';
          font-size: 32px;
          animation: spin 1.5s linear infinite;
        }

        .empty-state {
          padding: 80px 40px;
          text-align: center;
          color: #B8B8C5;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .empty-icon {
          font-size: 64px;
          opacity: 0.6;
        }

        .empty-state p {
          font-size: 16px;
          margin: 0;
          font-weight: 500;
        }

        .message-list {
          padding: 8px 0;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .message-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 16px 20px;
          border: 1px solid #EAEAEA;
          border-radius: 14px;
          cursor: pointer;
          transition: box-shadow .2s ease, transform .05s ease, background .2s ease;
          position: relative;
          background: #fff;
        }

        .message-item:hover {
          box-shadow: 0 4px 12px rgba(0,0,0,0.06);
          background: #fff;
        }

        .message-item.unread::before {
          content: '';
          position: absolute;
          left: 0;
          top: 10px;
          bottom: 10px;
          width: 3px;
          border-radius: 3px;
          background: #FFA87A;
        }

        .message-item.unread:hover {
          background: linear-gradient(135deg, rgba(255, 168, 122, 0.12) 0%, rgba(255, 168, 122, 0.06) 100%);
        }

        .message-icon {
          font-size: 20px;
          margin-right: 6px;
          flex-shrink: 0;
        }

        .message-content {
          flex: 1;
          min-width: 0;
        }

        .message-title {
          font-weight: 600;
          color: #172239;
          margin: 0;
          font-size: 15px;
          line-height: 1.6;
          white-space: normal;
          overflow: visible;
          word-wrap: break-word;
          letter-spacing: -0.01em;
        }

        .message-item.unread .message-title {
          color: #172239;
          font-weight: 700;
          font-size: 16px;
        }

        .message-preview {
          color: #718096;
          font-size: 14px;
          line-height: 1.5;
          margin-bottom: 6px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .message-time {
          color: #6D6D78;
          font-size: 13px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 4px;
          white-space: nowrap;
          margin-left: 8px;
          letter-spacing: -0.01em;
        }
        .message-time-right {
          margin-left: 12px;
        }

        .message-time::before {
          content: '🕒';
          font-size: 10px;
        }

        .unread-dot {
          width: 8px;
          height: 8px;
          background: #FF6B35;
          border-radius: 50%;
          margin-left: 8px;
          flex-shrink: 0;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes slideUp {
          from { 
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to { 
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }

        @keyframes glow {
          from { box-shadow: 0 2px 8px rgba(255, 107, 53, 0.4); }
          to { box-shadow: 0 2px 16px rgba(255, 107, 53, 0.6); }
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* 响应式设计 */
        @media (max-width: 480px) {
          .message-modal {
            width: 92vw;
            max-height: 70vh;
            margin: 12px;
          }
          .message-modal-header {
            padding: 12px 14px;
          }
          .message-item {
            padding: 12px 14px;
          }
        }
      `}</style>
    </div>
  );
}