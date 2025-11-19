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
from ai_chat.models import UserStudyPlan
from django.contrib.auth.models import User

def debug_plan_issue():
    """调试为什么没有显示plan内容"""
    print("🔍 调试plan显示问题")
    print("=" * 50)
    
    # 获取测试学生
    account = StudentAccount.objects.first()
    if not account:
        print("❌ 没有找到测试学生")
        return
    
    print(f"📝 学生ID: {account.student_id}")
    
    # 检查Django User
    try:
        user, _ = User.objects.get_or_create(
            username=account.student_id,
            defaults={'email': account.email or f'{account.student_id}@temp.com'}
        )
        print(f"✅ Django User: {user}")
    except Exception as e:
        print(f"❌ Django User创建失败: {e}")
        return
    
    # 检查学习计划
    print("\n📋 检查学习计划数据:")
    plans = UserStudyPlan.objects.filter(user=user)
    print(f"   总计划数: {plans.count()}")
    
    for i, plan in enumerate(plans, 1):
        print(f"\n   计划 {i}:")
        print(f"   ID: {plan.id}")
        print(f"   是否活跃: {plan.is_active}")
        print(f"   创建时间: {plan.created_at}")
        print(f"   数据键: {list(plan.plan_data.keys()) if plan.plan_data else 'None'}")
        
        if plan.is_active and plan.plan_data:
            overall_reason = plan.plan_data.get('overall_reason', '未找到')
            ai_summary = plan.plan_data.get('aiSummary', {})
            tasks = ai_summary.get('tasks', [])
            
            print(f"   overall_reason: {overall_reason[:100]}...")
            print(f"   任务数量: {len(tasks)}")
            
            for j, task in enumerate(tasks, 1):
                task_title = task.get('taskTitle', 'Unknown')
                parts = task.get('parts', [])
                print(f"     任务 {j}: {task_title} ({len(parts)} parts)")
    
    # 获取当前活跃计划
    current_plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()
    print(f"\n🎯 当前活跃计划: {current_plan.id if current_plan else 'None'}")
    
    if current_plan:
        print("📄 当前计划数据结构:")
        import json
        print(json.dumps(current_plan.plan_data, indent=2, ensure_ascii=False))
    
    # 测试AI服务获取计划
    print(f"\n🤖 测试AI服务:")
    service = AIChatService()
    plan_data = service.get_user_study_plan(account)
    
    if plan_data:
        print("✅ AI服务成功获取计划数据")
        print(f"   数据键: {list(plan_data.keys())}")
        print(f"   overall_reason: {plan_data.get('overall_reason', '未找到')[:50]}...")
    else:
        print("❌ AI服务没有获取到计划数据")
    
    # 测试对话逻辑
    print(f"\n💬 测试对话逻辑:")
    test_message = "Explain my plan"
    print(f"   测试消息: {test_message}")
    
    try:
        result = service.process_message(account, test_message)
        if result.get('success'):
            ai_response = result.get('ai_response', {})
            content = ai_response.get('content', '')
            intent = ai_response.get('intent', '')
            
            print(f"   处理成功: ✅")
            print(f"   意图: {intent}")
            print(f"   回复内容: {content[:200]}...")
            
            # 检查是否包含plan相关内容
            if 'plan' in content.lower() or 'study plan' in content.lower():
                print("   ✅ 回复包含plan相关内容")
            else:
                print("   ❌ 回复不包含plan相关内容")
        else:
            print(f"   处理失败: {result.get('error')}")
            
    except Exception as e:
        print(f"   处理异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_plan_issue()