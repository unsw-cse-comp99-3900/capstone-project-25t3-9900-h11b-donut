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

def debug_specific_issue():
    """调试具体的why plan问题"""
    print("🔍 调试具体的why plan问题")
    print("=" * 50)
    
    account = StudentAccount.objects.first()
    service = AIChatService()
    
    if not account:
        print("❌ 没有找到测试学生")
        return
    
    print(f"📝 学生ID: {account.student_id}")
    
    # 先进入study_plan_qna模式
    print("\n🎯 步骤1: 进入study_plan_qna模式")
    result1 = service.process_message(account, "Explain my plan")
    print(f"✅ 结果: {result1.get('success')}")
    
    if result1.get('success'):
        ai_response = result1.get('ai_response', {})
        current_mode = service.get_current_mode(account.student_id)
        print(f"🎯 当前模式: {current_mode}")
        print(f"📄 回复: {ai_response.get('content', '')[:200]}...")
    
    # 测试why plan询问
    print(f"\n🎯 步骤2: 询问why plan")
    result2 = service.process_message(account, "Why did you give me this plan?")
    print(f"✅ 结果: {result2.get('success')}")
    
    if result2.get('success'):
        ai_response = result2.get('ai_response', {})
        content = ai_response.get('content', '')
        intent = ai_response.get('intent', '')
        
        print(f"🎯 意图: {intent}")
        print(f"📄 回复: {content[:300]}...")
        
        # 检查是否是错误消息
        if "I don't see an active study plan" in content:
            print("❌ 检测到错误：没有找到计划")
            
            # 手动检查各个获取方法
            print(f"\n🔍 手动检查各获取方法:")
            
            # 检查get_current_plan_for_user
            plan1 = service.get_current_plan_for_user(account)
            print(f"   get_current_plan_for_user: {'有数据' if plan1 else '无数据'}")
            
            # 检查get_user_study_plan
            plan2 = service.get_user_study_plan(account)
            print(f"   get_user_study_plan: {'有数据' if plan2 else '无数据'}")
            
            # 比较两个方法的结果
            if plan1 and plan2:
                print("   ✅ 两个方法都返回数据")
                print(f"   plan1 keys: {list(plan1.keys())}")
                print(f"   plan2 keys: {list(plan2.keys())}")
            elif plan1:
                print("   ⚠️ 只有plan1返回数据")
            elif plan2:
                print("   ⚠️ 只有plan2返回数据")
            else:
                print("   ❌ 两个方法都无数据")
            
            # 检查plan数据结构
            if plan1:
                overall_reason = plan1.get('overall_reason')
                ai_summary = plan1.get('aiSummary')
                print(f"   overall_reason: {overall_reason is not None}")
                print(f"   aiSummary: {ai_summary is not None}")
                
                if ai_summary:
                    tasks = ai_summary.get('tasks')
                    print(f"   tasks: {tasks is not None and len(tasks) > 0}")
            
    else:
        print(f"❌ 处理失败: {result2.get('error')}")

if __name__ == "__main__":
    debug_specific_issue()