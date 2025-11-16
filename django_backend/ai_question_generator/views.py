"""
AI Question Generator & Grader Views
提供API接口用于题目生成和自动评分
"""
import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import SampleQuestion, GeneratedQuestion, StudentAnswer
from .generator import QuestionGenerator
from .grader import AutoGrader


# ==================== 示例题目管理 ====================

@csrf_exempt
@require_http_methods(["POST"])
def upload_sample_questions(request):
    """
    Admin上传示例题目
    
    POST /api/ai/sample-questions/upload
    Body: {
        "course_code": "COMP9900",
        "topic": "Python Data Structures",
        "difficulty": "medium",
        "questions": [
            {
                "type": "mcq",
                "question": "What is...",
                "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
                "correct_answer": "A",
                "explanation": "...",
                "score": 10
            },
            {
                "type": "short_answer",
                "question": "Explain...",
                "sample_answer": "...",
                "grading_points": ["point1", "point2"],
                "score": 10
            }
        ]
    }
    
    Response: {
        "success": true,
        "message": "Uploaded 2 sample questions",
        "question_ids": [1, 2]
    }
    """
    try:
        data = json.loads(request.body)
        course_code = data.get('course_code')
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'medium')
        questions = data.get('questions', [])
        
        if not course_code or not topic:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: course_code, topic'
            }, status=400)
        
        created_ids = []
        admin_id = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'admin'
        
        for q in questions:
            sample_q = SampleQuestion.objects.create(
                course_code=course_code,
                topic=topic,
                difficulty=difficulty,
                question_type=q.get('type'),
                question_text=q.get('question'),
                options=q.get('options'),
                correct_answer=q.get('correct_answer'),
                explanation=q.get('explanation'),
                sample_answer=q.get('sample_answer'),
                grading_points=q.get('grading_points'),
                score=q.get('score', 10),
                created_by=admin_id
            )
            created_ids.append(sample_q.id)
        
        return JsonResponse({
            'success': True,
            'message': f'Uploaded {len(created_ids)} sample questions',
            'question_ids': created_ids
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_sample_questions(request):
    """
    获取示例题目列表（用于Admin查看）
    
    GET /api/ai/sample-questions?course_code=COMP9900&topic=Python
    
    Response: {
        "success": true,
        "questions": [...]
    }
    """
    try:
        course_code = request.GET.get('course_code')
        topic = request.GET.get('topic')
        
        filters = {'is_active': True}
        if course_code:
            filters['course_code'] = course_code
        if topic:
            filters['topic__icontains'] = topic
        
        questions = SampleQuestion.objects.filter(**filters).values()
        
        return JsonResponse({
            'success': True,
            'questions': list(questions)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== AI题目生成 ====================

@csrf_exempt
@require_http_methods(["POST"])
def generate_questions(request):
    """
    AI生成题目
    
    POST /api/ai/questions/generate
    Body: {
        "course_code": "COMP9900",
        "topic": "Machine Learning Basics",
        "difficulty": "medium",
        "count": 5,
        "mcq_count": 3,
        "short_answer_count": 2
    }
    
    Response: {
        "success": true,
        "session_id": "uuid-...",
        "questions": [
            {
                "id": 1,
                "type": "mcq",
                "question": "...",
                "options": [...],
                "score": 10
            },
            ...
        ],
        "total_questions": 5
    }
    """
    try:
        data = json.loads(request.body)
        course_code = data.get('course_code')
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'medium')
        count = data.get('count', 5)
        mcq_count = data.get('mcq_count', 3)
        short_answer_count = data.get('short_answer_count', 2)
        
        if not course_code or not topic:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: course_code, topic'
            }, status=400)
        
        # 从数据库获取示例题目
        sample_questions = SampleQuestion.objects.filter(
            course_code=course_code,
            is_active=True
        ).order_by('-created_at')[:10]  # 最多取10个示例
        
        if not sample_questions.exists():
            return JsonResponse({
                'success': False,
                'error': f'No sample questions found for course {course_code}. Please upload sample questions first.'
            }, status=404)
        
        # 转换为生成器需要的格式
        sample_data = []
        for sq in sample_questions:
            q_data = {
                'type': sq.question_type,
                'question': sq.question_text,
                'score': sq.score
            }
            if sq.question_type == 'mcq':
                q_data.update({
                    'options': sq.options,
                    'correct_answer': sq.correct_answer,
                    'explanation': sq.explanation
                })
            else:
                q_data.update({
                    'sample_answer': sq.sample_answer,
                    'grading_points': sq.grading_points
                })
            sample_data.append(q_data)
        
        # 初始化生成器并生成题目
        generator = QuestionGenerator()
        generated = generator.generate_questions(
            topic=topic,
            difficulty=difficulty,
            sample_questions=sample_data,
            count=count,
            mcq_count=mcq_count,
            short_answer_count=short_answer_count
        )
        
        if not generated:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate questions'
            }, status=500)
        
        # 创建会话ID并保存到数据库
        session_id = str(uuid.uuid4())
        
        saved_questions = []
        for idx, q in enumerate(generated, 1):
            gen_q = GeneratedQuestion.objects.create(
                session_id=session_id,
                course_code=course_code,
                topic=topic,
                difficulty=difficulty,
                question_type=q.get('type'),
                question_data=q
            )
            
            # 添加数据库ID到返回的题目中
            q['db_id'] = gen_q.id
            q['question_id'] = idx  # 前端显示用的序号
            saved_questions.append(q)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'questions': saved_questions,
            'total_questions': len(saved_questions)
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


# ==================== 学生答题与评分 ====================

@csrf_exempt
@require_http_methods(["POST"])
def submit_answers(request):
    """
    学生提交答案并获取AI评分
    
    POST /api/ai/answers/submit
    Body: {
        "session_id": "uuid-...",
        "student_id": "z1234567",
        "answers": [
            {
                "question_db_id": 1,
                "answer": "A"
            },
            {
                "question_db_id": 2,
                "answer": "Learning rate controls..."
            }
        ]
    }
    
    Response: {
        "success": true,
        "grading_results": [
            {
                "question_id": 1,
                "question_db_id": 1,
                "type": "mcq",
                "student_answer": "A",
                "score": 10,
                "max_score": 10,
                "is_correct": true,
                "feedback": "..."
            },
            {
                "question_id": 2,
                "question_db_id": 2,
                "type": "short_answer",
                "student_answer": "...",
                "score": 7.5,
                "max_score": 10,
                "breakdown": {
                    "Correctness": 3,
                    "Completeness": 3,
                    "Clarity": 2
                },
                "feedback": "...",
                "hint": "...",
                "solution": "..."
            }
        ],
        "total_score": 17.5,
        "total_max_score": 20,
        "percentage": 87.5
    }
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        answers = data.get('answers', [])
        
        if not session_id or not student_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: session_id, student_id'
            }, status=400)
        
        # 获取该会话的所有题目
        questions = GeneratedQuestion.objects.filter(session_id=session_id).order_by('id')
        
        if not questions.exists():
            return JsonResponse({
                'success': False,
                'error': f'No questions found for session {session_id}'
            }, status=404)
        
        # 构建题目映射
        question_map = {q.id: q for q in questions}
        
        # 准备评分数据
        questions_for_grading = []
        student_answers_dict = {}
        
        for ans in answers:
            q_db_id = ans.get('question_db_id')
            answer_text = ans.get('answer', '')
            
            if q_db_id in question_map:
                q = question_map[q_db_id]
                q_data = q.question_data.copy()
                q_data['id'] = q_db_id
                q_data['type'] = q.question_type
                questions_for_grading.append(q_data)
                student_answers_dict[str(q_db_id)] = answer_text
        
        # 初始化评分器
        grader = AutoGrader()
        
        # 硬编码的评分细则（与grader.py保持一致）
        rubric = {
            "mcq": {
                "correct": 10,
                "incorrect": 0,
                "partial_credit": False
            },
            "short_answer": {
                "criteria": [
                    {"name": "Correctness", "max_points": 4},
                    {"name": "Completeness", "max_points": 4},
                    {"name": "Clarity", "max_points": 2}
                ],
                "total_points": 10
            }
        }
        
        # 评分
        grading_result = grader.grade_all(
            questions_for_grading,
            student_answers_dict,
            student_id
        )
        
        # 保存学生答案和评分结果到数据库
        graded_at = timezone.now()
        for result in grading_result['grading_results']:
            q_db_id = result['question_id']
            StudentAnswer.objects.create(
                session_id=session_id,
                student_id=student_id,
                question_id=q_db_id,
                answer_text=student_answers_dict.get(str(q_db_id), ''),
                grading_result=result,
                graded_at=graded_at
            )
        
        # 为每个结果添加question_db_id
        for result in grading_result['grading_results']:
            result['question_db_id'] = result['question_id']
        
        return JsonResponse({
            'success': True,
            'student_id': grading_result['student_id'],
            'grading_results': grading_result['grading_results'],
            'total_score': grading_result['total_score'],
            'total_max_score': grading_result['total_max_score'],
            'percentage': grading_result['percentage']
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_http_methods(["GET"])
def get_student_results(request):
    """
    获取学生的答题历史
    
    GET /api/ai/results?student_id=z1234567&session_id=uuid-...
    
    Response: {
        "success": true,
        "results": [...]
    }
    """
    try:
        student_id = request.GET.get('student_id')
        session_id = request.GET.get('session_id')
        
        if not student_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field: student_id'
            }, status=400)
        
        filters = {'student_id': student_id}
        if session_id:
            filters['session_id'] = session_id
        
        answers = StudentAnswer.objects.filter(**filters).select_related('question').order_by('-submitted_at')
        
        results = []
        for ans in answers:
            results.append({
                'id': ans.id,
                'session_id': ans.session_id,
                'question_id': ans.question.id,
                'question_data': ans.question.question_data,
                'answer_text': ans.answer_text,
                'grading_result': ans.grading_result,
                'submitted_at': ans.submitted_at.isoformat(),
                'graded_at': ans.graded_at.isoformat() if ans.graded_at else None
            })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
