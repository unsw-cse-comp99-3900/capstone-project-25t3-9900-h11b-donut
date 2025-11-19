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
from ai_chat.models import UserStudyPlan, StudyPlanQnAState
from django.contrib.auth.models import User

def deep_debug():
    """深度调试plan获取问题"""
    print("🔍 深度调试plan获取问题")
    print("=" * 60)
    
    # 1. 检查所有StudentAccount
    print("📋 1. 检查所有StudentAccount:")
    accounts = StudentAccount.objects.all()
    print(f"   总数: {accounts.count()}")
    
    for i, acc in enumerate(accounts[:3], 1):  # 只显示前3个
        print(f"   {i}. {acc.student_id} - {acc.name} - {acc.email}")
    
    # 选择第一个进行详细测试
    if not accounts.exists():
        print("❌ 没有任何StudentAccount")
        return
    
    account = accounts.first()
    print(f"\n🎯 选择测试账户: {account.student_id}")
    
    # 2. 检查对应的Django User
    print(f"\n👤 2. 检查Django User:")
    users = User.objects.filter(username=account.student_id)
    print(f"   找到User数量: {users.count()}")
    
    if users.exists():
        user = users.first()
        print(f"   User ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
    else:
        print("   ❌ 没有找到对应的Django User")
        # 创建User
        user, created = User.objects.get_or_create(
            username=account.student_id,
            defaults={'email': account.email or f'{account.student_id}@temp.com'}
        )
        print(f"   {'✅ 创建新User' if created else '✅ 获取现有User'}: {user.id}")
    
    # 3. 检查所有UserStudyPlan
    print(f"\n📊 3. 检查UserStudyPlan:")
    all_plans = UserStudyPlan.objects.all()
    print(f"   总计划数: {all_plans.count()}")
    
    for i, plan in enumerate(all_plans[:3], 1):
        print(f"   {i}. User: {plan.user.username if plan.user else 'None'} - 活跃: {plan.is_active} - 创建: {plan.created_at}")
    
    # 4. 检查当前账户的计划
    print(f"\n🎯 4. 检查当前账户的计划:")
    user_plans = UserStudyPlan.objects.filter(user=user)
    print(f"   该用户的计划数: {user_plans.count()}")
    
    active_plans = user_plans.filter(is_active=True)
    print(f"   活跃计划数: {active_plans.count()}")
    
    if active_plans.exists():
        active_plan = active_plans.first()
        print(f"   活跃计划ID: {active_plan.id}")
        print(f"   活跃计划创建时间: {active_plan.created_at}")
        
        if active_plan.plan_data:
            print(f"   计划数据键: {list(active_plan.plan_data.keys())}")
            overall_reason = active_plan.plan_data.get('overall_reason', 'None')
            print(f"   overall_reason存在: {overall_reason is not None}")
            if overall_reason:
                print(f"   overall_reason长度: {len(str(overall_reason))}")
        else:
            print("   ❌ 计划数据为空")
    else:
        print("   ❌ 没有活跃计划")
        
        # 检查是否有非活跃计划
        inactive_plans = user_plans.filter(is_active=False)
        if inactive_plans.exists():
            print(f"   有 {inactive_plans.count()} 个非活跃计划")
            # 激活第一个
            first_plan = inactive_plans.first()
            first_plan.is_active = True
            first_plan.save()
            print(f"   ✅ 已激活计划 {first_plan.id}")
    
    # 5. 测试AI服务的各种获取方法
    print(f"\n🤖 5. 测试AI服务获取方法:")
    service = AIChatService()
    
    # 方法1: get_user_study_plan
    plan1 = service.get_user_study_plan(account)
    print(f"   get_user_study_plan: {'有数据' if plan1 else '无数据'}")
    
    # 方法2: get_current_plan_for_user  
    plan2 = service.get_current_plan_for_user(account)
    print(f"   get_current_plan_for_user: {'有数据' if plan2 else '无数据'}")
    
    # 比较结果
    if plan1 and plan2:
        print("   ✅ 两个方法都返回数据")
        if plan1 == plan2:
            print("   ✅ 两个方法返回相同数据")
        else:
            print("   ⚠️ 两个方法返回不同数据")
    elif plan1:
        print("   ⚠️ 只有方法1返回数据")
    elif plan2:
        print("   ⚠️ 只有方法2返回数据")
    else:
        print("   ❌ 两个方法都无数据")
    
    # 6. 直接测试错误情况
    print(f"\n🧪 6. 测试错误场景:")
    
    # 清除状态重新测试
    StudyPlanQnAState.objects.filter(student_id=account.student_id).delete()
    
    test_message = "Why did you give me this plan?"
    print(f"   测试消息: {test_message}")
    
    result = service.process_message(account, test_message)
    
    if result.get('success'):
        ai_response = result.get('ai_response', {})
        content = ai_response.get('content', '')
        
        print(f"   处理成功")
        print(f"   AI回复: {content[:200]}...")
        
        if "I don't see an active study plan" in content:
            print("   ❌ 检测到错误：没有找到计划")
            
            # 强制创建计划数据
            print("   🔧 尝试强制创建计划数据...")
            test_plan_data = {
                "overall_reason": "This plan is designed to help you complete your assignments efficiently while balancing your workload.",
                "aiSummary": {
                    "tasks": [
                        {
                            "taskTitle": "Database Design Assignment",
                            "parts": [
                                {
                                    "label": "Schema design",
                                    "detail": "Design database schema with proper normalization and relationships.",
                                    "why_in_plan": "This is foundation and needs to be completed first."
                                }
                            ]
                        }
                    ]
                }
            }
            
            # 保存计划
            if service.save_study_plan(account, test_plan_data):
                print("   ✅ 强制创建计划成功")
                
                # 重新测试
                result2 = service.process_message(account, test_message)
                if result2.get('success'):
                    content2 = result2.get('ai_response', {}).get('content', '')
                    print(f"   重新测试结果: {content2[:200]}...")
                    
                    if "Great question" in content2:
                        print("   ✅ 重新测试成功！")
                    else:
                        print("   ❌ 重新测试仍然失败")
        else:
            print("   ✅ 没有检测到错误")
    else:
        print(f"   ❌ 处理失败: {result.get('error')}")

if __name__ == "__main__":
    deep_debug()