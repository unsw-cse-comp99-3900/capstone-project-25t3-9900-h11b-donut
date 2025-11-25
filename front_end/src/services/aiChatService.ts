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
   * Send a message to AI and receive a reply
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken(),
      };
      
      // Add authentication token
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // Get current user ID - Do not use default value, there must be a real user ID
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        throw new Error('User not logged in, unable to send messages');
      }
      const url = `${this.baseUrl}/chat/?user_id=${encodeURIComponent(currentUserId)}`;
      
      console.log('📡 Send AI request:', { message, currentUserId, url, token: token ? 'exists' : 'missing' });
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        console.error('❌ AI request failed:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI response successful:', data);
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
   * Get conversation history
   */
  async getChatHistory(limit: number = 50, days?: number): Promise<ChatHistoryResponse> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        console.error('❌ User not logged in');
        throw new Error('User not logged in, unable to retrieve historical messages');
      }
      
      // Build URL parameters
      const params = new URLSearchParams({
        limit: limit.toString(),
        user_id: currentUserId
      });
      
      // if days are specified, add the days parameter
      if (days !== undefined) {
        params.append('days', days.toString());
      }
      
      const url = `${this.baseUrl}/chat/?${params.toString()}`;
      
      console.log('📡 Retrieve historical message requests:', { currentUserId, url, limit, days, headers });
      console.log('🔍 completed URL:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        credentials: 'include',
      });

      console.log('📡 response status:', { 
        ok: response.ok, 
        status: response.status, 
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ AI request failed:', { 
          status: response.status, 
          statusText: response.statusText,
          errorBody: errorText
        });
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Historical message response:', { 
        success: data.success, 
        messageCount: data.messages?.length || 0,
        userId: currentUserId
      });
      return data;
    } catch (error) {
      console.error('❌ Error fetching chat history:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        console.error('🔥 Network connection failure - possible reasons:');
        console.error('  1. Backend service not started');
        console.error('  2. CORS configuration issue');
        console.error('  3. Proxy configuration issue');
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
   * Save learning plan data to AI dialogue module
   */
  async saveStudyPlan(planData: any): Promise<{ success: boolean; error?: string }> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken(),
      };
      
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const currentUserId = localStorage.getItem('current_user_id');
      if (!currentUserId) {
        throw new Error('User not logged in, unable to save study plan');
      }
      
      const url = `${this.baseUrl}/study-plan/?user_id=${encodeURIComponent(currentUserId)}`;
      
      console.log('📡 Save study plan request:', { currentUserId, url });
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ plan_data: planData }),
      });

      if (!response.ok) {
        console.error('❌ AI request failed:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI response successful:', data);
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
   * get currenct plan
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
        console.error('❌ AI request failed:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI response successful:', data);
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
   * Clean up old conversation records
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
        console.error('❌ AI request failed:', { status: response.status, statusText: response.statusText });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ AI response successful:', data);
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
   * Check if a greeting message needs to be sent (re-enter after 6 hours)
   */
  async shouldSendGreeting(): Promise<boolean> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      

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
        return true; // Default greeting sent when an error occurs
      }

      const data = await response.json();
      return data.should_send_greeting === true;
    } catch (error) {
      console.error('Greeting check failed:', error);
      return true; // Default greeting sent when an error occurs
    }
  }

  /**
   * Check the health status of AI services
   */
  async healthCheck(): Promise<boolean> {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
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
   * get CSRF Token
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
*Format timestamp to readable format
*/
/**
*Get date label (for grouping)
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
   * Group messages by date
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
    
    // Sort by date (latest below)
    const sortedGroups = Object.entries(groups).map(([date, msgs]) => ({
      date,
      messages: msgs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }));
    
    //Sort the groups
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
      
      // Get today's start time（00:00:00）
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      
      // Calculate the difference in days
      const daysDiff = Math.floor((today.getTime() - messageDate.getTime()) / (1000 * 60 * 60 * 24));
      
      // today
      if (daysDiff === 0) {
        return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // yesterday
      if (daysDiff === 1) {
        return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // within this week
      if (daysDiff >= 2 && daysDiff <= 6) {
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
        return `${dayName} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
      
      // more earlier
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      }) + ` ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } catch (error) {
      console.error('Timestamp formatting error:', error);
      return '';
    }
  }

  /**
   * Processing suggestion: Click to send preset message directly
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

export const aiChatService = new AIChatService();