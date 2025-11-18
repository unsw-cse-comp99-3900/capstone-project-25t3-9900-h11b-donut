#!/usr/bin/env python3
"""
简单测试2
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount

def simple_test():
    print("开始简单测试...")
    
    # 创建聊天服务实例
    service = AIChatService()
    
    # 模拟用户ID
    user_id = "z1234567"
    
    # 创建或获取用户账户
    try:
        account = StudentAccount.objects.get(student_id=user_id)
    except StudentAccount.DoesNotExist:
        account = StudentAccount(
            student_id=user_id,
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        account.save()
    
    print("用户账户创建成功")
    
    # 设置练习模式
    service.set_practice_setup_mode(user_id, 'course')
    print("练习模式设置成功")
    
    # 第一次调用
    print("开始第一次调用...")
    try:
        response = service.process_message(account, "I want to practice COMP9417")
        print("第一次调用成功")
        print("响应类型:", type(response))
        print("响应键:", response.keys() if isinstance(response, dict) else "Not a dict")
    except Exception as e:
        print(f"第一次调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 检查课程主题
    print("检查COMP9417的课程主题...")
    topics = service.get_course_topics("COMP9417")
    print("可用主题:", topics)
    
    # 第二次调用
    print("开始第二次调用...")
    try:
        response2 = service.process_message(account, "goals")
        print("第二次调用成功")
        print("响应2类型:", type(response2))
        if isinstance(response2, dict) and 'ai_response' in response2:
            content = response2['ai_response'].get('content', '')
            print("响应内容:", content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"第二次调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("测试完成")

if __name__ == "__main__":
    simple_test()