// 测试AI问题生成器服务的简单脚本
import { aiQuestionService } from './services/aiQuestionService';

// 测试生成练习题目
async function testGenerateQuestions() {
  console.log('🧪 开始测试AI问题生成器...');
  
  try {
    const result = await aiQuestionService.generatePracticeQuestions(
      'CS101',
      ['binary search', 'data structures'],
      3
    );
    
    if (result.success) {
      console.log('✅ AI题目生成成功!');
      console.log('题目数量:', result.data?.questions.length);
      console.log('Session ID:', result.data?.session_id);
      console.log('题目示例:', result.data?.questions[0]);
    } else {
      console.error('❌ AI题目生成失败:', result.error);
    }
  } catch (error) {
    console.error('❌ 测试过程中发生错误:', error);
  }
}

// 测试获取示例题目
async function testGetSampleQuestions() {
  console.log('🧪 开始测试获取示例题目...');
  
  try {
    const result = await aiQuestionService.getSampleQuestionsByTopic('CS101', 'binary search');
    
    if (result.success) {
      console.log('✅ 示例题目获取成功!');
      console.log('题目数量:', result.data?.length);
    } else {
      console.error('❌ 示例题目获取失败:', result.error);
    }
  } catch (error) {
    console.error('❌ 测试过程中发生错误:', error);
  }
}

// 导出测试函数
export { testGenerateQuestions, testGetSampleQuestions };

// 如果直接运行此文件，执行测试
if (typeof window === 'undefined') {
  // Node.js环境
  testGenerateQuestions();
  testGetSampleQuestions();
}