#!/usr/bin/env python3

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount

def test_plan_content_display():
    """测试计划内容显示"""
    print("🔍 测试计划内容显示")
    print("=" * 40)
    
    account = StudentAccount.objects.first()
    service = AIChatService()
    
    if not account:
        print("❌ 没有找到测试学生")
        return
    
    # 测试完整的对话流程
    test_messages = [
        "Explain my plan",  # 应该显示欢迎消息
        "Why did you give me this plan?",  # 应该显示整体原因
        "Explain Task 1 – Part A.",  # 应该显示具体内容
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 测试 {i}: {message}")
        
        try:
            result = service.process_message(account, message)
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                
                print(f"✅ 处理成功")
                print(f"🎯 意图: {intent}")
                print(f"📄 回复内容:")
                print(content[:500] + ("..." if len(content) > 500 else ""))
                
                # 分析内容
                content_lower = content.lower()
                if "welcome" in content_lower and "explain" in content_lower:
                    print("💡 这是欢迎引导消息")
                elif "great question" in content_lower and "main idea" in content_lower:
                    print("💡 这是计划整体解释")
                elif "sure! let's look at" in content_lower:
                    print("💡 这是具体Task/Part解释")
                elif "i'm not sure" in content_lower:
                    print("💡 这是错误提示")
                else:
                    print("💡 未知类型的回复")
                    
            else:
                print(f"❌ 处理失败: {result.get('error')}")
                
        except Exception as e:
            print(f"💥 异常: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_plan_content_display()