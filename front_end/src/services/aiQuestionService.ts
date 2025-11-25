//AI Problem Generator Service
//Used to connect the front-end with the AI problem generator API

import api from './api';

// TypeScript interface definition
export interface GenerateRequest {
  course_code: string;
  topic: string;
  question_count: number;
  question_types: ('multiple-choice' | 'short_answer')[];
  difficulty: 'easy' | 'medium' | 'hard';
  sample_questions?: number[]; 
}

export interface GeneratedQuestion {
  id: number;
  question_type: 'mcq' | 'short'; 
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
    question_db_id: number;  
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

//AI Problem Generator Service Class
class AIQuestionService {
  private baseUrl = '/ai';  // Remove the/pai prefix, as api.ts will automatically add it

  // AI generated questions (core function)
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

  // Submit answers and receive AI ratings
  async submitAnswers(data: SubmitAnswersRequest): Promise<ApiResponse<GradingResponse>> {
    try {
      console.log('🚀 [aiQuestionService] Submit answer request:', data);
      const response = await api.post(`${this.baseUrl}/answers/submit`, data);
      console.log('✅ [aiQuestionService] Submit answer response:', response);
      return response as ApiResponse<GradingResponse>;
    } catch (error: any) {
      console.error('❌ [aiQuestionService] fail to submit:', {
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

  // Obtain student answer history
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

  // A convenient method for generating exercise questions based on weak points
  async generatePracticeQuestions(
    courseCode: string,
    weakTopics: string[],
    questionCount: number = 5
  ): Promise<ApiResponse<GenerateResponse>> {
    // Generate questions for each weak point
    const requests: GenerateRequest[] = weakTopics.map(topic => ({
      course_code: courseCode,
      topic: topic,
      question_count: Math.ceil(questionCount / weakTopics.length),
      question_types: ['multiple-choice', 'short_answer'],
      difficulty: 'medium' as const
    }));

    try {
      // At present, we will handle the first topic first, and it can be expanded to merge multiple topics in the future
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

// Create service instance
export const aiQuestionService = new AIQuestionService();

export default aiQuestionService;