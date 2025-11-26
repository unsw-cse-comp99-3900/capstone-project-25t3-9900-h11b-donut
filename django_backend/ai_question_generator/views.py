"""
AI Question Generator & Grader Views
Provide API interface for question generation and automatic grading
"""
import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from dotenv import load_dotenv


from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

from .models import GeneratedQuestion, StudentAnswer
from .generator import QuestionGenerator
from .grader import AutoGrader



@csrf_exempt
@require_http_methods(["POST"])
def generate_questions(request):
    """
    AI question generating
    
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
        
        # Retrieve sample questions from the Question table of courses_admin
        from courses.models import Question, QuestionChoice, QuestionKeyword, QuestionKeywordMap
        
        # Firstly, try to search for relevant questions based on the keywords of the topic
        topic_lower = topic.lower()
        
        # Method 1: Search through keyword mapping
        keyword_matches = QuestionKeyword.objects.filter(name__icontains=topic_lower)
        if keyword_matches.exists():
            question_ids = QuestionKeywordMap.objects.filter(
                keyword__in=keyword_matches
            ).values_list('question_id', flat=True)
            sample_questions = Question.objects.filter(
                id__in=question_ids,
                course_code=course_code
            ).order_by('-created_at')[:10]
        else:
            # Method 2: Fuzzy matching through title and description
            sample_questions = Question.objects.filter(
                course_code=course_code
            ).filter(
                models.Q(title__icontains=topic) | 
                models.Q(description__icontains=topic) |
                models.Q(text__icontains=topic)
            ).order_by('-created_at')[:10]
        
        # If no relevant questions are found, obtain all questions for the course
        if not sample_questions.exists():
            sample_questions = Question.objects.filter(
                course_code=course_code
            ).order_by('-created_at')[:10]  
        
        if not sample_questions.exists():
            return JsonResponse({
                'success': False,
                'error': f'No questions found for course {course_code}. Please upload questions through the admin panel first.'
            }, status=404)
        
        # Convert to the format required by the generator
        sample_data = []
        for q in sample_questions:
            q_data = {
                'type': q.qtype,
                'question': q.text,
                'score': 10  
            }
            
            if q.qtype == 'mcq':
                # Get multiple-choice options
                choices = QuestionChoice.objects.filter(question=q).order_by('order')
                options = []
                correct_answer = ''
                
                for choice in choices:
                    option_text = f"{choice.label or chr(65 + choice.order)}. {choice.content}"
                    options.append(option_text)
                    if choice.is_correct:
                        correct_answer = choice.label or chr(65 + choice.order)
                
                q_data.update({
                    'options': options,
                    'correct_answer': correct_answer,
                    'explanation': q.description or f"Correct answer is {correct_answer}"
                })
            else:  # short answer
                q_data.update({
                    'sample_answer': q.short_answer or "Sample answer not available",
                    'grading_points': q.keywords_json or ["Content accuracy", "Clarity", "Completeness"]
                })
            
            sample_data.append(q_data)
        
        # Initialize the generator and generate questions
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
        
        # Create a session ID and save it to the database
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
            
            # Add database ID to the returned question
            q['db_id'] = gen_q.id
            q['question_id'] = idx  
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


@csrf_exempt
@require_http_methods(["POST"])
def submit_answers(request):
    """
    Students submit answers and receive AI ratings
    
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
        
        # Get all the questions for this session
        questions = GeneratedQuestion.objects.filter(session_id=session_id).order_by('id')
        
        if not questions.exists():
            return JsonResponse({
                'success': False,
                'error': f'No questions found for session {session_id}'
            }, status=404)
        
        # Build a question mapping
        question_map = {q.id: q for q in questions}
        
        # Prepare rating data
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
        
        # Initialize Scorer
        grader = AutoGrader()
        
        # Hard coded grading criteria (consistent with grader.py)
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
        
        # grading
        grading_result = grader.grade_all(
            questions_for_grading,
            student_answers_dict,
            student_id
        )
        
        # Save student answers and grading results to the database
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
        
        # Save to RecentPracticeSession for AI chat use
        try:
            from ai_chat.models import RecentPracticeSession
            
            # Get session information (course and topic) - obtained from model fields, not question_data
            first_question = questions.first()
            course_code = first_question.course_code if first_question else 'Unknown'
            topic = first_question.topic if first_question else 'General'
            
            # Build detailed test data
            test_data_for_ai = {
                "questions": []
            }
            
            for result in grading_result['grading_results']:
                q_db_id = result['question_id']
                question_obj = question_map.get(q_db_id)
                if question_obj:
                    q_detail = {
                        "question_text": question_obj.question_data.get('question', 'N/A'),
                        "question_type": result.get('type', 'unknown'),
                        "student_answer": result.get('student_answer', ''),
                        "correct_answer": question_obj.question_data.get('correct_answer', 'N/A'),
                        "score": result.get('score', 0),
                        "max_score": result.get('max_score', 10),
                        "is_correct": result.get('is_correct', False),
                        "feedback": result.get('feedback', '')
                    }
                    if result.get('type') == 'mcq' and 'options' in question_obj.question_data:
                        q_detail['options'] = question_obj.question_data.get('options', [])
                    test_data_for_ai["questions"].append(q_detail)
            
            # create/update RecentPracticeSession
            RecentPracticeSession.objects.update_or_create(
                student_id=student_id,
                session_id=session_id,
                defaults={
                    'course_code': course_code,
                    'topic': topic,
                    'total_score': grading_result['total_score'],
                    'max_score': grading_result['total_max_score'],
                    'percentage': grading_result['percentage'],
                    'questions_count': len(grading_result['grading_results']),
                    'test_data': test_data_for_ai,
                }
            )
            print(f"[DEBUG] The test results have been saved toRecentPracticeSession: {student_id} - {session_id}")
        except Exception as e:
            print(f"[WARNING] Failed to save to RecentPracticeSession: {e}")
            # Does not affect the main process, continue to return the rating results
        
        # Add questiond_db_id for each result
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
def get_session_questions(request, session_id):
    """
    Obtain questions for specific practice sessions
    
    GET /api/ai/questions/session/{session_id}
    
    Response: {
        "success": true,
        "questions": [...]
    }
    """
    try:
        questions = GeneratedQuestion.objects.filter(session_id=session_id).order_by('id')
        
        if not questions.exists():
            return JsonResponse({
                'success': False,
                'error': f'No questions found for session {session_id}'
            }, status=404)
        
        question_list = []
        for q in questions:
            # Return complete question information, including questionype and difficulty
            question_list.append({
                'id': q.id,  
                'question_type': q.question_type,  
                'question_data': q.question_data,  
                'difficulty': q.difficulty 
            })
        
        return JsonResponse({
            'success': True,
            'questions': question_list,
            'total_questions': len(question_list)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_student_results(request):
    """
    answer history of students
    
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
