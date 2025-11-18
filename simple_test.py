#!/usr/bin/env python3
"""
简单测试
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
    
    print("测试完成")

if __name__ == "__main__":
    simple_test()