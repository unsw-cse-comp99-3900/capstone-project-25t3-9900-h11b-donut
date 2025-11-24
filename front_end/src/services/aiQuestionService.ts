// AI问题生成器服务
// 用于连接前端与AI问题生成器API

import api from './api';

// TypeScript接口定义
export interface GenerateRequest {
  course_code: string;
  topic: string;
  question_count: number;
  question_types: ('multiple-choice' | 'short_answer')[];
  difficulty: 'easy' | 'medium' | 'hard';
  sample_questions?: number[]; // 示例题目ID列表
}

export interface GeneratedQuestion {
  id: number;
  question_type: 'mcq' | 'short';  // 后端使用的类型
  question_data: {
    question: string;
    type: 'mcq' | 'short';
    options?: string[];
    correct_answer?: string;
    explanation?: string;
    sample_answer?: string;
    grading_points?: string[];
    score?: number;
  };
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface GenerateResponse {
  session_id: string;
  questions: GeneratedQuestion[];
  total_questions: number;
  estimated_time: number;
}

export interface SubmitAnswersRequest {
  session_id: string;
  student_id: number;
  answers: {
    question_db_id: number;  // 后端期望 question_db_id
    answer: string;
    time_spent: number;
  }[];
}

export interface GradingResponse {
  session_id: string;
  total_score: number;
  max_score: number;
  percentage: number;
  feedback: string;
  detailed_feedback: {
    question_id: number;
    score: number;
    feedback: string;
    is_correct: boolean;
  }[];
  time_spent: number;
}

export interface StudentResult {
  id: number;
  session_id: string;
  student_id: number;
  total_score: number;
  max_score: number;
  percentage: number;
  feedback: string;
  time_spent: number;
  completed_at: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

// AI问题生成器服务类
class AIQuestionService {
  private baseUrl = '/ai';  // 去掉 /api 前缀，因为 api.ts 会自动添加

  // AI生成题目 (核心功能)
  async generateQuestions(data: GenerateRequest): Promise<ApiResponse<GenerateResponse>> {
    try {
      const response = await api.post(`${this.baseUrl}/questions/generate`, data);
      return response as ApiResponse<GenerateResponse>;
    } catch (error: any) {
      return {
        success: false,
        message: 'Failed to generate questions',
        error: error.response?.data?.error || error.message
      };
    }
  }

  // 提交答案并获取AI评分
  async submitAnswers(data: SubmitAnswersRequest): Promise<ApiResponse<GradingResponse>> {
    try {
      console.log('🚀 [aiQuestionService] 提交答案请求:', data);
      const response = await api.post(`${this.baseUrl}/answers/submit`, data);
      console.log('✅ [aiQuestionService] 提交答案响应:', response);
      // api.post 已经返回 ApiResponse 格式，直接返回即可
      return response as ApiResponse<GradingResponse>;
    } catch (error: any) {
      console.error('❌ [aiQuestionService] 提交答案失败:', {
        error: error.response?.data || error.message,
        status: error.response?.status,
        url: `${this.baseUrl}/answers/submit`
      });
      return {
        success: false,
        message: 'Failed to submit answers',
        error: error.response?.data?.error || error.message
      };
    }
  }

  // 获取学生答题历史
  async getStudentResults(params?: {
    student_id?: number;
    session_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<ApiResponse<{ results: StudentResult[], total: number }>> {
    try {
      const response = await api.get(`${this.baseUrl}/results`, params);
      return response as ApiResponse<{ results: StudentResult[], total: number }>;
    } catch (error: any) {
      return {
        success: false,
        message: 'Failed to fetch student results',
        error: error.response?.data?.error || error.message
      };
    }
  }

  // 根据薄弱项生成练习题目的便捷方法
  async generatePracticeQuestions(
    courseCode: string,
    weakTopics: string[],
    questionCount: number = 5
  ): Promise<ApiResponse<GenerateResponse>> {
    // 为每个薄弱项生成题目
    const requests: GenerateRequest[] = weakTopics.map(topic => ({
      course_code: courseCode,
      topic: topic,
      question_count: Math.ceil(questionCount / weakTopics.length),
      question_types: ['multiple-choice', 'short_answer'],
      difficulty: 'medium' as const
    }));

    try {
      // 目前先处理第一个topic，后续可以扩展为多个topic的合并
      const response = await this.generateQuestions(requests[0]);
      return response;
    } catch (error: any) {
      return {
        success: false,
        message: 'Failed to generate practice questions',
        error: error.message
      };
    }
  }
}

// 创建服务实例
export const aiQuestionService = new AIQuestionService();

// 导出默认实例
export default aiQuestionService;