#!/usr/bin/env python3
"""
调试测试
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

def debug_test():
    print("开始调试测试...")
    
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
    
    print("=== 测试 get_course_topics ===")
    topics = service.get_course_topics("COMP9417")
    print(f"COMP9417 主题: {topics}")
    
    print("=== 测试 validate_topic_input ===")
    is_valid, validated_topic = service.validate_topic_input("goals", topics)
    print(f"验证 'goals': {is_valid}, {validated_topic}")
    
    print("=== 测试 generate_practice_for_topic ===")
    result = service.generate_practice_for_topic("COMP9417", "goals")
    print(f"生成结果: {result[:200] if result else 'None'}")

if __name__ == "__main__":
    debug_test()