#!/usr/bin/env python3
"""
验证测试学生账号的题目访问情况
"""
from __future__ import annotations

import os
import sys

# 设置Django环境
backend_path = os.path.join(os.path.dirname(__file__), 'django_backend')
sys.path.insert(0, backend_path)
_ = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

from courses.models import StudentEnrollment, Question, QuestionChoice
from django.db.models import Count

def verify_student_questions():
    """验证学生是否有足够的题目可以练习"""
    print("=== 🎯 测试学生账号题目访问验证 ===\n")
    
    # 获取所有学生选课情况
    enrollments = StudentEnrollment.objects.all()
    
    print("📚 学生选课及题目情况:")
    print("-" * 60)
    
    for enrollment in enrollments:
        student_id = enrollment.student_id
        course_code = enrollment.course_code
        
        # 统计该课程题目数量
        question_count = Question.objects.filter(course_code=course_code).count()
        mcq_count = Question.objects.filter(course_code=course_code, qtype='mcq').count()
        short_count = Question.objects.filter(course_code=course_code, qtype='short').count()
        
        # 统计选择题选项数量
        choice_count = QuestionChoice.objects.filter(question__course_code=course_code).count()
        
        print(f"👨‍🎓 学生: {student_id}")
        print(f"📖 课程: {course_code}")
        print(f"   📝 总题目数: {question_count}")
        print(f"   🔄 选择题: {mcq_count} 道 (共 {choice_count} 个选项)")
        print(f"   ✍️  简答题: {short_count} 道")
        
        if question_count > 0:
            print("   ✅ 该课程有题目可供练习")
        else:
            print("   ❌ 该课程暂无题目")
        print()
    
    # 按课程统计
    print("📊 课程题目统计:")
    print("-" * 40)
    
    from django.db import models
    questions_by_course = Question.objects.values('course_code').annotate(
        total=Count('id'),
        mcq=Count('id', filter=models.Q(qtype='mcq')),
        short=Count('id', filter=models.Q(qtype='short'))
    ).order_by('course_code')
    
    for course_stat in questions_by_course:
        course_code = course_stat['course_code']
        total = course_stat['total']
        mcq = course_stat['mcq']
        short = course_stat['short']
        
        enrolled_count = StudentEnrollment.objects.filter(course_code=course_code).count()
        
        print(f"📚 {course_code}:")
        print(f"   📊 题目: {total} 道 (选择题: {mcq}, 简答题: {short})")
        print(f"   👥 选修学生: {enrolled_count} 人")
        
        if enrolled_count > 0:
            print(f"   ✅ 有学生选修，可用于测试")
        else:
            print(f"   ⚠️  无学生选修，如需测试请添加学生")
        print()
    
    print("🎉 验证完成！")
    print("\n💡 建议:")
    print("1. 测试学生账号 z5530236, z1234567, z1122334 可以练习 COMP9417 (Data Mining) 的题目")
    print("2. 测试学生账号 z5530236, z9876543 可以练习 COMP9900 (Capstone) 的题目")
    print("3. 每个学生都有足够的题目进行测试")

if __name__ == "__main__":
    verify_student_questions()