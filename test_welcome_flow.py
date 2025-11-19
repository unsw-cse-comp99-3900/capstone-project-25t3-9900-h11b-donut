#!/usr/bin/env python3
"""
测试Explain My Plan对话流程修复
验证用户发送Please explain my study plan for me后的响应
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount

def test_welcome_flow():
    """测试欢迎流程"""
    print("🧪 测试Explain My Plan欢迎流程")
    print("=" * 50)
    
    # 获取测试学生
    account = StudentAccount.objects.first()
    if not account:
        print("❌ 没有找到测试学生")
        return False
    
    service = AIChatService()
    
    # 清理之前的测试状态
    from ai_chat.models import StudyPlanQnAState
    StudyPlanQnAState.objects.filter(student_id=account.student_id).delete()
    
    print(f"📝 测试学生: {account.student_id}")
    
    # 测试场景
    test_messages = [
        {
            "name": "触发Explain My Plan",
            "message": "Please explain my study plan for me",
            "expect_welcome": True
        },
        {
            "name": "询问具体Task",
            "message": "Explain Task 1 – Part A.",
            "expect_welcome": False,
            "expect_task_detail": True
        },
        {
            "name": "再次触发Explain My Plan",
            "message": "Explain my plan",
            "expect_welcome": True
        }
    ]
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n🧪 测试 {i}/{len(test_messages)}: {test['name']}")
        print(f"📝 输入: '{test['message']}'")
        
        try:
            result = service.process_message(account, test['message'])
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                
                print(f"✅ 消息处理成功")
                print(f"🎯 意图: {intent}")
                print(f"📄 回复内容: {content[:150]}...")
                
                # 验证结果
                success = True
                
                if test.get('expect_welcome'):
                    if "Of course, I'd be happy to explain your study plan" in content:
                        print("✅ 正确显示欢迎消息")
                    else:
                        print("❌ 未显示欢迎消息")
                        success = False
                elif test.get('expect_task_detail'):
                    if "Sure! Let's look at" in content and "What this part is about:" in content:
                        print("✅ 正确显示Task详情")
                    else:
                        print("❌ 未显示Task详情")
                        success = False
                
                if success:
                    print("🎉 测试通过!")
                else:
                    print("❌ 测试失败!")
                    
            else:
                print(f"❌ 消息处理失败: {result.get('error')}")
                
        except Exception as e:
            print(f"💥 测试异常: {e}")
        
        print("-" * 40)
    
    print("\n✨ 测试完成!")
    return True

if __name__ == "__main__":
    test_welcome_flow()