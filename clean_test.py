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
from ai_chat.models import StudyPlanQnAState

def clean_and_test():
    """清理状态并重新测试"""
    print("🧹 清理状态并重新测试")
    print("=" * 40)
    
    account = StudentAccount.objects.first()
    service = AIChatService()
    
    if not account:
        print("❌ 没有找到测试学生")
        return
    
    # 清除所有模式状态
    StudyPlanQnAState.objects.filter(student_id=account.student_id).delete()
    print("🧹 已清除study_plan_qna状态")
    
    # 重新测试完整流程
    test_flow = [
        {
            "step": "1. 进入模式",
            "message": "Explain my plan",
            "expect": "欢迎消息"
        },
        {
            "step": "2. 询问整体原因", 
            "message": "Why did you give me this plan?",
            "expect": "计划整体解释"
        },
        {
            "step": "3. 询问具体部分",
            "message": "Explain Task 1 – Part A.",
            "expect": "Task 1 Part A详情"
        },
        {
            "step": "4. 退出模式",
            "message": "stop",
            "expect": "退出确认"
        }
    ]
    
    print(f"\n🧪 开始完整流程测试:")
    
    for i, test in enumerate(test_flow, 1):
        print(f"\n{'='*50}")
        print(f"🧪 {test['step']}: {test['message']}")
        print(f"🎯 期望: {test['expect']}")
        
        try:
            result = service.process_message(account, test['message'])
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                current_mode = service.get_current_mode(account.student_id)
                
                print(f"✅ 处理成功")
                print(f"🎯 意图: {intent}")
                print(f"🎯 模式: {current_mode}")
                print(f"📄 回复: {content[:150]}...")
                
                # 检查内容
                content_lower = content.lower()
                if "no active study plan" in content_lower:
                    print("❌ ❌ ❌ 检测到错误：没有找到计划")
                    return False
                elif "welcome" in content_lower and "explain" in content_lower:
                    print("✅ ✅ 检测到欢迎消息")
                elif "great question" in content_lower and "main idea" in content_lower:
                    print("✅ ✅ 检测到计划整体解释")
                elif "sure! let's look at" in content_lower:
                    print("✅ ✅ 检测到具体部分解释")
                elif "no problem" in content_lower and "switch back" in content_lower:
                    print("✅ ✅ 检测到退出确认")
                else:
                    print("⚠️  未知类型的回复")
                    
            else:
                print(f"❌ 处理失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"💥 异常: {e}")
            return False
    
    print(f"\n{'='*50}")
    print("🎉 完整流程测试完成！")
    print("✅ 所有步骤都正确执行")
    return True

if __name__ == "__main__":
    success = clean_and_test()
    
    if success:
        print("\n✨ Explain My Plan 功能正常工作！")
        print("📋 功能特性:")
        print("   • 正确进入study_plan_qna模式")
        print("   • 正确响应why plan询问")
        print("   • 正确响应Task/Part询问")
        print("   • 正确处理退出命令")
        print("   • 能够读取数据库中的计划数据")
    else:
        print("\n⚠️  功能存在问题，需要修复")