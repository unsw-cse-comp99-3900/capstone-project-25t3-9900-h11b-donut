#!/usr/bin/env python3
"""
调试澄清逻辑
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount

def debug_clarification():
    """调试澄清逻辑"""
    print("=== 调试澄清逻辑 ===\n")
    
    # 临时禁用Gemini以测试规则逻辑
    import ai_chat.chat_service as chat_service
    original_use_gemini = chat_service.use_gemini
    chat_service.use_gemini = False
    
    try:
        # 创建测试用户
        test_student = StudentAccount(
            student_id="z1234567",
            name="Test Student",
            email="test@example.com"
        )
        
        service = AIChatService()
        
        # 测试消息
        messages = [
            "I'm struggling with data structures",
            "I find sorting algorithms difficult"
        ]
        
        for message in messages:
            print(f"消息: '{message}'")
            
            # 检测意图
            intent = service.detect_intent(message)
            print(f"检测到的意图: {intent}")
            
            # 提取主题
            topic = service.extract_weak_topic(message)
            print(f"提取的主题: '{topic}'")
            
            # 检查主题是否具体
            is_specific = service.is_topic_specific(topic) if topic else False
            print(f"主题是否具体: {is_specific}")
            
            # 生成回复
            response = service.generate_ai_response(message, test_student)
            print(f"完整回复:\n{response}\n")
            print("=" * 80)
    
    finally:
        # 恢复原始设置
        chat_service.use_gemini = original_use_gemini

if __name__ == "__main__":
    debug_clarification()