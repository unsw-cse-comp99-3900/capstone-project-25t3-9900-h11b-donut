#!/usr/bin/env python3
"""
调试AI聊天服务中的练习生成调用
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService

def test_chat_service():
    print("=== 测试AI聊天服务练习生成 ===")
    
    # 创建聊天服务实例
    chat_service = AIChatService()
    
    # 测试生成练习
    print("调用 generate_practice_for_topic...")
    try:
        result = chat_service.generate_practice_for_topic('COMP9417', 'goals')
        print(f"返回结果: {result}")
        
        if "I've generated" in result:
            print("✅ 生成成功!")
            return True
        elif "Sorry, I encountered an issue" in result:
            print("❌ 生成失败!")
            return False
        else:
            print("⚠️ 返回了意外结果")
            return False
            
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chat_service()