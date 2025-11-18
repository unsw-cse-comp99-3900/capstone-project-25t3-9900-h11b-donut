#!/usr/bin/env python3
"""
创建测试题目数据到courses_admin的Question表
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List

# 设置Django环境
backend_path = os.path.join(os.path.dirname(__file__), 'django_backend')
sys.path.insert(0, backend_path)
_ = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

# 现在可以安全导入Django模型
# pyright: reportMissingImports=false
from courses.models import Question, QuestionChoice, QuestionKeyword, QuestionKeywordMap

def create_test_questions() -> None:
    """创建测试题目"""
    print("=== 创建测试题目 ===\n")
    
    # 创建测试题目 - 匹配实际存在的课程
    test_questions: List[Dict[str, str | list[str]]] = [
        # COMP9417 - Data Mining 题目
        {
            'course_code': 'COMP9417',
            'qtype': 'mcq',
            'title': 'Data Mining Basics',
            'description': 'Test understanding of data mining fundamental concepts',
            'text': 'What is the main goal of data mining?',
            'keywords': ['data mining', 'concepts', 'goals']
        },
        {
            'course_code': 'COMP9417',
            'qtype': 'mcq',
            'title': 'Classification Algorithms',
            'description': 'Test knowledge of classification methods in data mining',
            'text': 'Which algorithm is commonly used for classification tasks?',
            'keywords': ['data mining', 'classification', 'algorithms']
        },
        {
            'course_code': 'COMP9417',
            'qtype': 'short',
            'title': 'Clustering Definition',
            'description': 'Test understanding of clustering in data mining',
            'text': 'Explain what clustering is and provide one example of its application.',
            'short_answer': 'Clustering is the process of grouping similar data points together based on their characteristics. Example: customer segmentation in marketing.',
            'keywords': ['data mining', 'clustering', 'unsupervised learning']
        },
        
        # COMP9900 - Capstone 题目
        {
            'course_code': 'COMP9900',
            'qtype': 'mcq',
            'title': 'Project Planning',
            'description': 'Test knowledge of capstone project planning phases',
            'text': 'What is the first phase in capstone project development?',
            'keywords': ['capstone', 'project management', 'planning']
        },
        {
            'course_code': 'COMP9900',
            'qtype': 'short',
            'title': 'Team Collaboration',
            'description': 'Test understanding of teamwork in capstone projects',
            'text': 'Describe two key challenges in team collaboration for capstone projects and suggest solutions.',
            'short_answer': '1. Communication barriers: Solution - Use regular meetings and collaboration tools. 2. Uneven workload distribution: Solution - Clear task assignment and progress tracking.',
            'keywords': ['capstone', 'teamwork', 'collaboration']
        },
        
        # COMP9331 - Computer Network 题目
        {
            'course_code': 'COMP9331',
            'qtype': 'mcq',
            'title': 'Network Protocols',
            'description': 'Test knowledge of network communication protocols',
            'text': 'Which protocol operates at the transport layer?',
            'keywords': ['networking', 'protocols', 'osi model']
        },
        {
            'course_code': 'COMP9331',
            'qtype': 'short',
            'title': 'TCP vs UDP',
            'description': 'Test understanding of transport layer protocols',
            'text': 'Explain the main differences between TCP and UDP protocols.',
            'short_answer': 'TCP is connection-oriented, reliable, and guarantees delivery order. UDP is connectionless, faster, but does not guarantee delivery or order.',
            'keywords': ['networking', 'tcp', 'udp', 'transport layer']
        },
        
        # COMP1234 - Test 题目
        {
            'course_code': 'COMP1234',
            'qtype': 'mcq',
            'title': 'Software Testing Basics',
            'description': 'Test understanding of software testing fundamentals',
            'text': 'What is the purpose of unit testing?',
            'keywords': ['testing', 'unit testing', 'software quality']
        }
    ]
    
    created_questions: List[Question] = []
    
    for q_data in test_questions:
        # 创建题目
        question = Question.objects.create(
            course_code=q_data['course_code'],
            qtype=q_data['qtype'],
            title=q_data['title'],
            description=q_data['description'],
            text=q_data['text'],
            short_answer=q_data.get('short_answer', ''),
            keywords_json=q_data['keywords']
        )
        
        # 如果是选择题，创建选项
        if q_data['qtype'] == 'mcq':
            if 'Data Mining Basics' in q_data['title']:
                choices_data: List[Dict[str, str | bool]] = [
                    {'label': 'A', 'content': 'To store data efficiently', 'is_correct': False},
                    {'label': 'B', 'content': 'To discover patterns and knowledge from large datasets', 'is_correct': True},
                    {'label': 'C', 'content': 'To visualize data', 'is_correct': False},
                    {'label': 'D', 'content': 'To clean data only', 'is_correct': False}
                ]
            elif 'Classification Algorithms' in q_data['title']:
                choices_data = [
                    {'label': 'A', 'content': 'K-means', 'is_correct': False},
                    {'label': 'B', 'content': 'Decision Tree', 'is_correct': True},
                    {'label': 'C', 'content': 'PCA', 'is_correct': False},
                    {'label': 'D', 'content': 'Apriori', 'is_correct': False}
                ]
            elif 'Project Planning' in q_data['title']:
                choices_data = [
                    {'label': 'A', 'content': 'Implementation', 'is_correct': False},
                    {'label': 'B', 'content': 'Requirements gathering and analysis', 'is_correct': True},
                    {'label': 'C', 'content': 'Testing', 'is_correct': False},
                    {'label': 'D', 'content': 'Deployment', 'is_correct': False}
                ]
            elif 'Network Protocols' in q_data['title']:
                choices_data = [
                    {'label': 'A', 'content': 'HTTP', 'is_correct': False},
                    {'label': 'B', 'content': 'IP', 'is_correct': False},
                    {'label': 'C', 'content': 'TCP', 'is_correct': True},
                    {'label': 'D', 'content': 'Ethernet', 'is_correct': False}
                ]
            else:  # Software Testing Basics
                choices_data = [
                    {'label': 'A', 'content': 'To test individual components or functions', 'is_correct': True},
                    {'label': 'B', 'content': 'To test the entire system', 'is_correct': False},
                    {'label': 'C', 'content': 'To test user interface', 'is_correct': False},
                    {'label': 'D', 'content': 'To test performance', 'is_correct': False}
                ]
            
            for choice_data in choices_data:
                # 确保label是字符串类型
                label_str = str(choice_data['label'])
                QuestionChoice.objects.create(
                    question=question,
                    label=label_str,
                    order=int(ord(label_str) - ord('A')),
                    content=str(choice_data['content']),
                    is_correct=bool(choice_data['is_correct'])
                )
        
        created_questions.append(question)
        print(f"✅ 创建题目: {question.title}")
    
    print(f"\n总共创建了 {len(created_questions)} 道题目")
    
    # 创建关键词
    keywords: List[str] = ['data mining', 'concepts', 'goals', 'classification', 'algorithms', 'clustering', 'unsupervised learning', 'capstone', 'project management', 'planning', 'teamwork', 'collaboration', 'networking', 'protocols', 'osi model', 'tcp', 'udp', 'transport layer', 'testing', 'unit testing', 'software quality']
    created_keywords: Dict[str, QuestionKeyword] = {}
    
    for keyword in keywords:
        kw_obj, created = QuestionKeyword.objects.get_or_create(name=keyword)
        created_keywords[keyword] = kw_obj
        print(f"{'✅' if created else 'ℹ️'} 关键词: {keyword}")
    
    # 建立题目-关键词映射
    for question in created_questions:
        for keyword in question.keywords_json:
            if keyword in created_keywords:
                QuestionKeywordMap.objects.get_or_create(
                    question=question,
                    keyword=created_keywords[keyword]
                )
    
    print("\n=== 题目创建完成 ===")
    
    # 验证创建结果
    print(f"\n验证结果:")
    print(f"Question表: {Question.objects.count()} 道题目")
    print(f"QuestionChoice表: {QuestionChoice.objects.count()} 个选项")
    print(f"QuestionKeyword表: {QuestionKeyword.objects.count()} 个关键词")
    print(f"QuestionKeywordMap表: {QuestionKeywordMap.objects.count()} 个映射")

if __name__ == "__main__":
    create_test_questions()