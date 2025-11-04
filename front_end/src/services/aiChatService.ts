// AI对话服务 - 处理与后端AI对话API的交互
export interface ChatMessage {
  id: number;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  metadata?: any;
}

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
  async getChatHistory(limit: number = 50): Promise<ChatHistoryResponse> {
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
        throw new Error('用户未登录，无法发送消息');
      }
      const url = `${this.baseUrl}/chat/?limit=${limit}&user_id=${encodeURIComponent(currentUserId)}`;
      
      console.log('📡 获取历史消息请求:', { currentUserId, url, limit });
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
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
      console.error('Error fetching chat history:', error);
      return {
        success: false,
        messages: [],
        error: error instanceof Error ? error.message : 'Unknown error occurred',
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
      
      const response = await fetch(`${this.baseUrl}/study-plan/`, {
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
  formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (error) {
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