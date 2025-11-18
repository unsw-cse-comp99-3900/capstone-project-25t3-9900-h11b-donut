#!/usr/bin/env python3
"""
调试练习生成问题
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_question_generator.views import generate_questions
from django.http import HttpRequest

def test_practice_generation():
    print("=== 测试练习生成功能 ===")
    
    # 创建HTTP请求对象
    request = HttpRequest()
    request.method = 'POST'
    request._body = json.dumps({
        'course_code': 'COMP9417',
        'topic': 'goals',
        'difficulty': 'medium',
        'count': 5,
        'mcq_count': 3,
        'short_answer_count': 2
    }).encode('utf-8')
    request.content_type = 'application/json'
    request.META = {
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': str(len(request._body))
    }
    
    print("调用生成器...")
    try:
        response = generate_questions(request)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.content.decode('utf-8')}")
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"解析后的数据: {json.dumps(data, indent=2)}")
            return True
        else:
            print("生成失败")
            return False
            
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_practice_generation()