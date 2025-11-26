"""
AI Question Generator - Uses Gemini AI to generate questions
Django integrated version - Contains only core generation logic, all data transmitted via API
"""
import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
import google.generativeai as genai


from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


class QuestionGenerator:

    
    def __init__(self, api_key: str = None):

        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found, please set it in the environment variable")
        

        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
            }
        )
        
        # Configuration request timeout
        self.request_options = {
            'timeout': 120  # 120s
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
        Generate questions
        
        Args:
        Topic: Theme
        Difficulty: easy/medium/hard
        Sample_questions: List of sample questions
        Count: Total number of questions
        Mcq_comnt: Number of Multiple Choice Questions
        Short_answer_comnt: Number of short answer questions
                
        Returns:
        List of generated questions
        """
        # Build prompt words
        prompt = self._build_prompt(topic, difficulty, sample_questions, mcq_count, short_answer_count)
        
        # use Gemini API 
        response = self.model.generate_content(
            prompt,
            request_options=self.request_options
        )
        
        # Analyze response
        questions = self._parse_response(response.text, topic, difficulty)
        
        # Verification Question
        valid_questions = [q for q in questions if self._validate_question(q)]
        
        return valid_questions
    
    def _validate_question(self, question: Dict) -> bool:
        return 'type' in question and 'question' in question
    
    def _build_prompt(
        self, 
        topic: str, 
        difficulty: str,
        sample_questions: List[Dict],
        mcq_count: int,
        short_answer_count: int
    ) -> str:
        
       #Extract the theme of the example question
        sample_topic = "unknown"
        if sample_questions and len(sample_questions) > 0:
            sample_topic = sample_questions[0].get('topic', 'unknown')
        
        #Prepare sample question text
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
        
        #Remove possible markdown code block markers
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            # Extract code block content
            match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                
                cleaned = re.sub(r'^```(?:json)?[\s\n]*', '', cleaned)
                cleaned = re.sub(r'[\s\n]*```$', '', cleaned)
        
        # decode JSON
        questions = json.loads(cleaned)
        
        # Ensure that each question has necessary fields and enforce a score of 10 points
        for q in questions:
            q.setdefault('topic', topic)
            q.setdefault('difficulty', difficulty)
            # Mandatory 10 points per question to prevent AI from generating incorrect score values
            q['score'] = 10
        
        return questions
