"""
AI Auto-Grader - 使用 Gemini AI 自动评分
Django集成版本 - 仅包含核心评分逻辑，所有数据通过API传输
"""
import os
import json
import re
from typing import List, Dict
import google.generativeai as genai

# 从环境变量获取API密钥
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


class AutoGrader:
    """AI 自动评分器"""
    
    def __init__(self, api_key: str = None):
        """初始化评分器"""
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("未找到 GEMINI_API_KEY，请在环境变量中设置")
        
        # 配置 Gemini
        genai.configure(api_key=self.api_key)
        
        # 使用经过测试的可用模型，配置生成参数以提高一致性
        self.model = genai.GenerativeModel(
            'models/gemini-2.5-flash-preview-05-20',
            generation_config={
                'temperature': 0.1,
                'top_p': 0.8,
                'top_k': 10,
            }
        )
    
    def grade_mcq(self, question: Dict, student_answer: str) -> Dict:
        """
        评分选择题（直接比对）
        
        Args:
            question: 题目信息
            student_answer: 学生答案
        
        Returns:
            评分结果
        """
        correct_answer = question.get('correct_answer', '').strip().upper()
        student_answer_clean = student_answer.strip().upper()
        
        # 提取选项字母（处理 "A. ..." 或 "A" 格式）
        if '.' in student_answer_clean:
            student_answer_clean = student_answer_clean.split('.')[0].strip()
        if '.' in correct_answer:
            correct_answer = correct_answer.split('.')[0].strip()
        
        is_correct = student_answer_clean == correct_answer
        score = question.get('score', 10) if is_correct else 0
        
        return {
            'question_id': question.get('id'),
            'type': 'mcq',
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'score': score,
            'max_score': question.get('score', 10),
            'feedback': question.get('explanation', '') if is_correct else f"Incorrect. The correct answer is {correct_answer}. {question.get('explanation', '')}"
        }
    
    def grade_short_answer(self, question: Dict, student_answer: str, rubric: Dict = None) -> Dict:
        """
        使用 AI 评分简答题
        
        Args:
            question: 题目信息
            student_answer: 学生答案
            rubric: 评分细则（可选，使用默认评分标准）
        
        Returns:
            评分结果
        """
        # 构建评分提示词
        prompt = self._build_grading_prompt(question, student_answer)
        
        try:
            # 调用 Gemini API
            response = self.model.generate_content(prompt)
            
            # 解析评分结果
            result = self._parse_grading_response(response.text, question, student_answer)
            
            return result
            
        except Exception as e:
            # 返回默认评分
            return {
                'question_id': question.get('id'),
                'type': 'short_answer',
                'student_answer': student_answer,
                'score': 0,
                'max_score': question.get('score', 10),
                'feedback': f'Grading failed: {str(e)}',
                'breakdown': {}
            }
    
    def _build_grading_prompt(self, question: Dict, student_answer: str) -> str:
        """构建评分提示词"""
        
        max_score = question.get('score', 10)
        key_points = question.get('grading_points', [])
        key_points_text = "\n".join(f"- {p}" for p in key_points)
        sample_answer = question.get('sample_answer', 'Not provided')
        
        prompt = f"""You are a CONSISTENT and OBJECTIVE grader for educational assessments. You must grade deterministically - identical answers should always receive identical scores.

**CRITICAL GRADING RULES**:
1. Use the detailed rubric below to assign scores (0-4 for each criterion)
2. Award partial credit based on specific descriptors
3. Be CONSISTENT - same answer quality = same score every time
4. Base scores ONLY on observable evidence in the student's answer
5. Generate personalized hint and solution based on student's specific mistakes

═══════════════════════════════════════════════════════════

**Question**: {question.get('question')}

**Reference Answer**: {sample_answer}

**Required Key Points**:
{key_points_text}

**Student Answer**: {student_answer}

═══════════════════════════════════════════════════════════

**DETAILED GRADING RUBRIC**:

**Correctness (0-4 points)**:
- 0: Incorrect - The answer is fundamentally wrong or completely off-topic, with no meaningful overlap with the correct concepts.
- 1: Limited correctness - Only a few correct ideas appear. Several important concepts are misunderstood, mixed up, or incorrectly explained.
- 2: Partially correct - Some key ideas are correct, but parts of the answer are vague, slightly inaccurate, or somewhat confused. The overall direction is partly right but not fully reliable.
- 3: Mostly correct - Most key ideas are correct and consistent with the reference answer. There may be minor imprecision or small gaps, but no serious conceptual errors.
- 4: Fully correct - The answer is conceptually accurate and aligned with the reference answer. All mentioned key ideas are correct; no major misunderstandings or contradictions.

**Completeness (0-4 points)**:
- 0: Not complete - The answer does not meaningfully cover any of the expected key ideas.
- 1: Minimally complete - The answer mentions only a small number of expected key ideas (around 1-39%). Coverage is very partial and feels incomplete.
- 2: Partially complete - The answer covers some expected key ideas (around 40-59%). Several important ideas are missing or only hinted at.
- 3: Largely complete - The answer covers many expected key ideas (around 60-79%), but a few important ideas are missing or only briefly mentioned.
- 4: Fully complete - The answer covers almost all of the expected key ideas (around 80-100% of them). No major idea from the marking guide is missing.

**Clarity (0-2 points)**:
- 0: Hard to understand - The answer is poorly structured or very confusing. Sentences are fragmented or disorganized, with serious grammar or wording problems that make the meaning difficult to follow.
- 1: Generally understandable - The main idea can be understood, but the answer may be loosely structured, somewhat repetitive, or contain awkward phrasing and minor grammar issues.
- 2: Clear and well-structured - The answer is easy to read and follow. Sentences are coherent, the logic is sensible, and ideas are organized. Language issues, if any, do not hinder understanding.

**Total Score**: Sum of Correctness + Completeness + Clarity (Maximum: 10 points)

═══════════════════════════════════════════════════════════

**GRADING PROCESS**:

Step 1: Analyze the student answer against each criterion
Step 2: Assign scores (Correctness: 0-4, Completeness: 0-4, Clarity: 0-2)
Step 3: Calculate total_score = Correctness + Completeness + Clarity
Step 4: Identify specific gaps or errors in the student's answer
Step 5: Generate a personalized HINT that addresses the student's specific weaknesses without giving away the full answer
Step 6: Generate a SOLUTION that explains what the student missed and how to improve

**OUTPUT FORMAT** (MUST be valid JSON, no extra text):
{{
  "breakdown": {{
    "Correctness": <0-4>,
    "Completeness": <0-4>,
    "Clarity": <0-2>
  }},
  "total_score": <sum_of_above>,
  "feedback": "Detailed feedback explaining the score with specific references to what was correct/incorrect/missing",
  "hint": "Personalized hint based on student's specific mistakes (guide them without revealing the answer)",
  "solution": "Step-by-step explanation of what the student should have included and why"
}}

**HINT GENERATION GUIDELINES**:
- If student got 0-2 points: Provide fundamental concepts they need to review
- If student got 3-5 points: Point to specific missing key points
- If student got 6-8 points: Suggest refinements and additional details
- If student got 9-10 points: Offer advanced insights or alternative perspectives

**SOLUTION GENERATION GUIDELINES**:
- Explain each missing key point from grading_points
- Show how the reference answer addresses these points
- Provide concrete examples or explanations
- Structure as step-by-step guidance

**CONSTRAINTS**:
- Use numbers only (int), NO strings for scores
- Correctness: 0, 1, 2, 3, or 4
- Completeness: 0, 1, 2, 3, or 4
- Clarity: 0, 1, or 2
- total_score MUST equal sum of breakdown scores
- total_score MUST NOT exceed {max_score}
- Return ONLY the JSON object, nothing else
- Be CONSISTENT and DETERMINISTIC

Begin grading:"""
        
        return prompt
    
    def _parse_grading_response(self, response_text: str, question: Dict, student_answer: str) -> Dict:
        """解析 AI 评分响应"""
        
        # 提取 JSON
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                cleaned = re.sub(r'^```(?:json)?[\s\n]*', '', cleaned)
                cleaned = re.sub(r'[\s\n]*```$', '', cleaned)
        
        # 解析 JSON
        grading_result = json.loads(cleaned)
        
        # 构建标准格式结果
        return {
            'question_id': question.get('id'),
            'type': 'short_answer',
            'student_answer': student_answer,
            'score': grading_result.get('total_score', 0),
            'max_score': question.get('score', 10),
            'feedback': grading_result.get('feedback', ''),
            'breakdown': grading_result.get('breakdown', {}),
            'hint': grading_result.get('hint', ''),
            'solution': grading_result.get('solution', '')
        }
    
    def grade_all(self, questions: List[Dict], student_answers: Dict, student_id: str = 'unknown') -> Dict:
        """
        评分所有题目
        
        Args:
            questions: 题目列表
            student_answers: 学生答案字典 {question_id: answer}
            student_id: 学生ID
        
        Returns:
            完整评分结果
        """
        results = []
        
        for q in questions:
            qid = q.get('id')
            student_ans = student_answers.get(str(qid), '')
            
            if not student_ans:
                results.append({
                    'question_id': qid,
                    'type': q.get('type'),
                    'student_answer': '',
                    'score': 0,
                    'max_score': q.get('score', 10),
                    'feedback': 'No answer provided'
                })
                continue
            
            # 根据题型评分
            if q.get('type') == 'mcq':
                result = self.grade_mcq(q, student_ans)
            else:
                result = self.grade_short_answer(q, student_ans)
            
            results.append(result)
        
        # 计算总分
        total_score = sum(r.get('score', 0) for r in results)
        total_max = sum(r.get('max_score', 0) for r in results)
        
        return {
            'student_id': student_id,
            'grading_results': results,
            'total_score': total_score,
            'total_max_score': total_max,
            'percentage': (total_score / total_max * 100) if total_max > 0 else 0
        }
