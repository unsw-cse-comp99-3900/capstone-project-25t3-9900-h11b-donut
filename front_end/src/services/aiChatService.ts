// AI对话服务 - 处理与后端AI对话API的交互
export interface ChatMessage {
  id: number;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: string;
  metadata?: any;
}

export interface PracticeReadyMessage extends ChatMessage {
  messageType: 'practice_ready';
  practiceInfo: {
    course: string;
    topic: string;
    sessionId: string;
    totalQuestions: number;
  };
}

export type ChatMessageWithPractice = ChatMessage | PracticeReadyMessage;

export interface ChatResponse {
  success: boolean;
  user_message?: ChatMessage;
  ai_response?: ChatMessage;
  error?: string;
}

export interface ChatHistoryResponse {
  success: boolean;
  messages: ChatMessage[];
  error?: string;
  messageCount?: number;
  userId?: string;
}

class AIChatService {
  private baseUrl = '/api/ai';

  /**
   * 发送消息到AI并获取回复
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken(),
      };
      
      // 添加认证token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // 获取当前用户ID - 不使用默认值，必须有真实用户ID
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        throw new Error('用户未登录，无法发送消息');
      }
      const url = `${this.baseUrl}/chat/?user_id=${encodeURIComponent(currentUserId)}`;
      
      console.log('📡 发送AI请求:', { message, currentUserId, url, token: token ? 'exists' : 'missing' });
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        console.error('❌ AI请求失败:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI响应成功:', data);
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * 获取对话历史
   */
  async getChatHistory(limit: number = 50, days?: number): Promise<ChatHistoryResponse> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // 添加认证token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // 获取当前用户ID - 不使用默认值，必须有真实用户ID
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        console.error('❌ 用户未登录');
        throw new Error('用户未登录，无法获取历史消息');
      }
      
      // 构建URL参数
      const params = new URLSearchParams({
        limit: limit.toString(),
        user_id: currentUserId
      });
      
      // 如果指定了天数，添加days参数
      if (days !== undefined) {
        params.append('days', days.toString());
      }
      
      const url = `${this.baseUrl}/chat/?${params.toString()}`;
      
      console.log('📡 获取历史消息请求:', { currentUserId, url, limit, days, headers });
      console.log('🔍 完整URL:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        credentials: 'include',
      });

      console.log('📡 响应状态:', { 
        ok: response.ok, 
        status: response.status, 
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ AI请求失败:', { 
          status: response.status, 
          statusText: response.statusText,
          errorBody: errorText
        });
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ 历史消息响应:', { 
        success: data.success, 
        messageCount: data.messages?.length || 0,
        userId: currentUserId
      });
      return data;
    } catch (error) {
      console.error('❌ Error fetching chat history:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        console.error('🔥 网络连接失败 - 可能原因:');
        console.error('  1. 后端服务未启动');
        console.error('  2. CORS 配置问题');
        console.error('  3. 代理配置问题');
      }
      return {
        success: false,
        messages: [],
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        messageCount: 0,
        userId: localStorage.getItem('current_user_id') || ''
      };
    }
  }

  /**
   * 保存学习计划数据到AI对话模块
   */
  async saveStudyPlan(planData: any): Promise<{ success: boolean; error?: string }> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken(),
      };
      
      // 添加认证token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // 获取当前用户ID
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        throw new Error('用户未登录，无法保存学习计划');
      }
      
      const url = `${this.baseUrl}/study-plan/?user_id=${encodeURIComponent(currentUserId)}`;
      
      console.log('📡 保存学习计划请求:', { currentUserId, url });
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ plan_data: planData }),
      });

      if (!response.ok) {
        console.error('❌ AI请求失败:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI响应成功:', data);
      return data;
    } catch (error) {
      console.error('Error saving study plan:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * 获取当前学习计划
   */
  async getStudyPlan(): Promise<{ success: boolean; plan_data?: any; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/study-plan/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        console.error('❌ AI请求失败:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI响应成功:', data);
      return data;
    } catch (error) {
      console.error('Error fetching study plan:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * 清理旧的对话记录
   */
  async cleanupOldData(): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/cleanup/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        console.error('❌ AI请求失败:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI响应成功:', data);
      return data;
    } catch (error) {
      console.error('Error cleaning up old data:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * 检查是否需要发送问候消息（6小时后重新进入）
   */
  async shouldSendGreeting(): Promise<boolean> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // 添加认证token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/greeting-check/`, {
        method: 'GET',
        headers,
        credentials: 'include',
      });

      if (!response.ok) {
        return true; // 出错时默认发送问候
      }

      const data = await response.json();
      return data.should_send_greeting === true;
    } catch (error) {
      console.error('Greeting check failed:', error);
      return true; // 出错时默认发送问候
    }
  }

  /**
   * 检查AI服务健康状态
   */
  async healthCheck(): Promise<boolean> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // 添加认证token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/health/`, {
        method: 'GET',
        headers,
        credentials: 'include',
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      return data.success === true;
    } catch (error) {
      console.error('AI service health check failed:', error);
      return false;
    }
  }

  /**
   * 获取CSRF Token
   */
  private getCsrfToken(): string {
    const name = 'csrftoken';
    let cookieValue = '';
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * 格式化时间戳为可读格式
   */
  /**
   * 获取日期标签（用于分组）
   */
  getDateLabel(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      
      const daysDiff = Math.floor((today.getTime() - messageDate.getTime()) / (1000 * 60 * 60 * 24));
      
      if (daysDiff === 0) return 'Today';
      if (daysDiff === 1) return 'Yesterday';
      if (daysDiff >= 2 && daysDiff <= 6) {
        return date.toLocaleDateString('en-US', { weekday: 'long' });
      }
      
      return date.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric',
        year: 'numeric'
      });
    } catch (error) {
      return '';
    }
  }

  /**
   * 按日期分组消息
   */
  groupMessagesByDate(messages: ChatMessage[]): { date: string; messages: ChatMessage[] }[] {
    const groups: { [key: string]: ChatMessage[] } = {};
    
    messages.forEach(message => {
      const dateLabel = this.getDateLabel(message.timestamp);
      if (!groups[dateLabel]) {
        groups[dateLabel] = [];
      }
      groups[dateLabel].push(message);
    });
    
    // 按日期排序（最新的在下面）
    const sortedGroups = Object.entries(groups).map(([date, msgs]) => ({
      date,
      messages: msgs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }));
    
    // 对分组进行排序
    return sortedGroups.sort((a, b) => {
      const dateA = a.messages[0] ? new Date(a.messages[0].timestamp) : new Date(0);
      const dateB = b.messages[0] ? new Date(b.messages[0].timestamp) : new Date(0);
      return dateA.getTime() - dateB.getTime();
    });
  }

  formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      
      // 获取今天的开始时间（00:00:00）
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      
      // 计算天数差
      const daysDiff = Math.floor((today.getTime() - messageDate.getTime()) / (1000 * 60 * 60 * 24));
      
      // 今天
      if (daysDiff === 0) {
        return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // 昨天
      if (daysDiff === 1) {
        return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // 本周内（2-6天前）
      if (daysDiff >= 2 && daysDiff <= 6) {
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
        return `${dayName} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // 更早的日期，显示完整日期
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      }) + ` ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } catch (error) {
      console.error('时间戳格式化错误:', error);
      return '';
    }
  }

  /**
   * 处理建议点击 - 直接发送预设消息
   */
  async handleSuggestionClick(suggestion: string): Promise<ChatResponse> {
    let message = '';
    
    switch (suggestion) {
      case 'Explain my plan':
        message = 'Please explain my plan for me.';
        break;
      case 'Practice my weak topics':
        message = 'I really couldn\'t understand some topics and they are so hard for me. I want to do a practice of this part.';
        break;
      case 'How to do for Part N of Task X':
        message = 'How should I approach Part 2 of Task "Final Project Report"?';
        break;
      case 'Give me some encouragement':
        message = 'Give me some encouragement.';
        break;
      default:
        message = suggestion;
    }
    
    return this.sendMessage(message);
  }
}

// 导出单例实例
export const aiChatService = new AIChatService();