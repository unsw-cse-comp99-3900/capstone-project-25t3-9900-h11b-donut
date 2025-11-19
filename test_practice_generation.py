#!/usr/bin/env python
"""测试练习生成功能"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_question_generator.generator import QuestionGenerator
from courses.models import Question, QuestionChoice, QuestionKeyword, QuestionKeywordMap

def test_practice_generation():
    """测试练习生成"""
    course = "COMP9417"
    topic = "clustering"
    
    print(f"[TEST] 测试练习生成: course={course}, topic={topic}")
    
    # 获取示例题目
    topic_lower = topic.lower()
    
    # 方法1: 通过关键词查找
    print(f"[TEST] 方法1: 通过关键词查找...")
    keyword_maps = QuestionKeywordMap.objects.filter(
        keyword__name__icontains=topic_lower
    ).select_related('question')
    
    sample_questions_objs = [km.question for km in keyword_maps if km.question.course_code == course]
    print(f"[TEST] 通过关键词找到 {len(sample_questions_objs)} 个题目")
    
    # 方法2: 如果没找到,尝试直接匹配课程
    if not sample_questions_objs:
        print(f"[TEST] 方法2: 直接匹配课程...")
        sample_questions_objs = list(Question.objects.filter(
            course_code=course,
            is_active=True
        )[:5])
        print(f"[TEST] 通过课程找到 {len(sample_questions_objs)} 个题目")
    
    # 转换为字典格式
    sample_questions = []
    for q in sample_questions_objs[:5]:
        q_dict = {
            'type': q.qtype,
            'question': q.text,
            'topic': topic,
            'difficulty': 'medium',
            'score': 10
        }
        
        if q.qtype == 'mcq':
            choices = QuestionChoice.objects.filter(question=q)
            q_dict['options'] = [c.content for c in choices]
            correct_choice = choices.filter(is_correct=True).first()
            if correct_choice:
                q_dict['correct_answer'] = correct_choice.label or 'A'
            q_dict['explanation'] = q.description or ''
        else:
            q_dict['sample_answer'] = q.short_answer or ''
            if q.keywords_json:
                q_dict['grading_points'] = q.keywords_json if isinstance(q.keywords_json, list) else []
            else:
                q_dict['grading_points'] = []
        
        sample_questions.append(q_dict)
    
    print(f"[TEST] 准备了 {len(sample_questions)} 个示例题目")
    
    # 调用AI生成器
    try:
        print(f"[TEST] 初始化 QuestionGenerator...")
        generator = QuestionGenerator()
        
        print(f"[TEST] 调用 generate_questions...")
        generated_questions = generator.generate_questions(
            topic=topic,
            difficulty='medium',
            sample_questions=sample_questions,
            count=5,
            mcq_count=3,
            short_answer_count=2
        )
        
        print(f"[TEST] ✅ 成功生成了 {len(generated_questions)} 个题目")
        for idx, q in enumerate(generated_questions, 1):
            print(f"  {idx}. {q.get('type')}: {q.get('question')[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 生成题目失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_practice_generation()
    sys.exit(0 if success else 1)
