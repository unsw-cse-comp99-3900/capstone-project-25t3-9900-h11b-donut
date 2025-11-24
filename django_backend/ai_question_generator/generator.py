"""
AI Question Generator - 使用 Gemini AI 生成题目
Django集成版本 - 仅包含核心生成逻辑，所有数据通过API传输
"""
import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
import google.generativeai as genai

# 加载环境变量
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# 从环境变量获取API密钥
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


class QuestionGenerator:
    """AI 题目生成器"""
    
    def __init__(self, api_key: str = None):
        """初始化生成器"""
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("未找到 GEMINI_API_KEY，请在环境变量中设置")
        
        # 配置 Gemini
        genai.configure(api_key=self.api_key)
        
        # 使用可用的Gemini模型，配置生成参数
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
            }
        )
        
        # 配置请求超时
        self.request_options = {
            'timeout': 120  # 设置120秒超时
        }
    
    def generate_questions(
        self, 
        topic: str, 
        difficulty: str,
        sample_questions: List[Dict],
        count: int = 5,
        mcq_count: int = 3,
        short_answer_count: int = 2
    ) -> List[Dict]:
        """
        生成题目
        
        Args:
            topic: 主题
            difficulty: 难度 (easy/medium/hard)
            sample_questions: 示例题目列表
            count: 总题目数量
            mcq_count: 选择题数量
            short_answer_count: 简答题数量
        
        Returns:
            生成的题目列表
        """
        # 构建提示词
        prompt = self._build_prompt(topic, difficulty, sample_questions, mcq_count, short_answer_count)
        
        # 调用 Gemini API (使用超时配置)
        response = self.model.generate_content(
            prompt,
            request_options=self.request_options
        )
        
        # 解析响应
        questions = self._parse_response(response.text, topic, difficulty)
        
        # 验证题目
        valid_questions = [q for q in questions if self._validate_question(q)]
        
        return valid_questions
    
    def _validate_question(self, question: Dict) -> bool:
        """验证题目格式"""
        return 'type' in question and 'question' in question
    
    def _build_prompt(
        self, 
        topic: str, 
        difficulty: str,
        sample_questions: List[Dict],
        mcq_count: int,
        short_answer_count: int
    ) -> str:
        """构建 Gemini 提示词"""
        
        # 提取示例题目的主题
        sample_topic = "unknown"
        if sample_questions and len(sample_questions) > 0:
            sample_topic = sample_questions[0].get('topic', 'unknown')
        
        # 准备示例题目文本
        samples_text = ""
        for idx, sq in enumerate(sample_questions[:2], 1):
            samples_text += f"\nExample {idx}:\n"
            samples_text += f"Type: {sq.get('type', 'N/A')}\n"
            samples_text += f"Question: {sq.get('question', 'N/A')}\n"
            if sq.get('type') == 'mcq':
                samples_text += f"Options: {sq.get('options', [])}\n"
                samples_text += f"Correct Answer: {sq.get('correct_answer', 'N/A')}\n"
                samples_text += f"Explanation: {sq.get('explanation', 'N/A')}\n"
            else:
                samples_text += f"Sample Answer: {sq.get('sample_answer', 'N/A')}\n"
            samples_text += f"Hint: {sq.get('hint', 'N/A')}\n"
        
        prompt = f"""You are an expert question generator for educational assessments.

**CRITICAL INSTRUCTION**: 
- The example questions below are about "{sample_topic}"
- You MUST generate NEW questions about "{topic}" (DIFFERENT topic!)
- ONLY mimic the STYLE, FORMAT, and DIFFICULTY of the examples
- DO NOT copy the content or subject matter from the examples

═══════════════════════════════════════════════════════════

**Your Task**: 
Generate {mcq_count + short_answer_count} high-quality questions specifically about "{topic}" with difficulty level "{difficulty}".

**What to Mimic from Examples**:
✅ Question structure and phrasing style
✅ Difficulty level and complexity
✅ Question format (MCQ vs short-answer)
✅ Level of detail in explanations
✅ Hint style

**What NOT to Copy**:
❌ Subject matter or content
❌ Specific concepts from the example topic
❌ Example-specific terminology

**Requirements**:
1. Generate {mcq_count} multiple-choice questions (MCQ) about {topic}
2. Generate {short_answer_count} short-answer questions about {topic}
3. Match the difficulty level: {difficulty}
4. Questions must be clear, unambiguous, and test understanding of {topic}
5. For MCQs: provide 4 options (A, B, C, D), mark the correct answer, and provide explanation
6. For short-answer: provide a sample answer, grading key points, and a hint

**Style Reference - Examples from "{sample_topic}"**:{samples_text}

═══════════════════════════════════════════════════════════

**Output Format** (strict JSON array):
[
  {{
    "id": 1,
    "type": "mcq",
    "question": "Your question about {topic}...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "A",
    "explanation": "Detailed explanation...",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "score": 10
  }},
  {{
    "id": 2,
    "type": "short_answer",
    "question": "Your question about {topic}...",
    "sample_answer": "Complete reference answer that demonstrates full understanding...",
    "grading_points": ["Key point 1", "Key point 2", "Key point 3", "Key point 4"],
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "score": 10
  }}
]

**CRITICAL SCORING REQUIREMENT**: 
- EVERY question MUST have "score": 10 (exactly 10 points)
- DO NOT use any other score value
- This is MANDATORY and NON-NEGOTIABLE

**IMPORTANT**: 
- DO NOT include "hint" field in the output
- For short_answer questions, provide comprehensive sample_answer and specific grading_points
- Grading points should be clear, measurable criteria

**Final Checklist**:
- [ ] All questions are about "{topic}" (NOT "{sample_topic}")
- [ ] Difficulty matches "{difficulty}"
- [ ] Format and style match the examples
- [ ] Valid JSON format
- [ ] {mcq_count} MCQs + {short_answer_count} short-answer = {mcq_count + short_answer_count} total

Generate the questions now:"""
        
        return prompt
    
    def _parse_response(self, response_text: str, topic: str, difficulty: str) -> List[Dict]:
        """解析 Gemini 响应"""
        
        # 移除可能的 markdown 代码块标记
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            # 提取代码块内容
            match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                # 移除开头和结尾的```
                cleaned = re.sub(r'^```(?:json)?[\s\n]*', '', cleaned)
                cleaned = re.sub(r'[\s\n]*```$', '', cleaned)
        
        # 解析 JSON
        questions = json.loads(cleaned)
        
        # 确保每个题目都有必要的字段，并强制score为10分
        for q in questions:
            q.setdefault('topic', topic)
            q.setdefault('difficulty', difficulty)
            # 🔥 强制每题10分，防止AI生成错误的score值
            q['score'] = 10
        
        return questions
