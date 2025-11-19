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

# 使用现有学生
account = StudentAccount.objects.first()
print(f"📝 使用学生: {account.student_id}")

# 检查是否有学习计划
try:
    user, _ = User.objects.get_or_create(
        username=account.student_id,
        defaults={'email': account.email or f'{account.student_id}@temp.com'}
    )
    
    plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()
    if plan:
        print(f"✅ 找到学习计划: {plan}")
        print(f"📋 计划数据键: {list(plan.plan_data.keys())}")
    else:
        print("❌ 没有找到活跃的学习计划")
        print("🔄 创建测试计划...")
        
        # 创建测试计划
        from ai_chat.models import UserStudyPlan
        
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
                            },
                            {
                                "label": "SQL implementation", 
                                "detail": "Implement designed schema using SQL DDL statements.",
                                "why_in_plan": "After designing schema, you need to create it in database."
                            }
                        ]
                    }
                ]
            }
        }
        
        # 将之前的计划设为非活跃
        UserStudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # 创建新计划
        UserStudyPlan.objects.create(
            user=user,
            plan_data=test_plan_data,
            is_active=True
        )
        
        print("✅ 测试计划创建完成")
        
except Exception as e:
    print(f"💥 检查学习计划时出错: {e}")
    import traceback
    traceback.print_exc()

# 测试AI服务
service = AIChatService()

print("\n🔍 测试模式识别功能:")

test_messages = [
    "Explain my plan",
    "Please explain my study plan", 
    "why did you give me this plan?",
    "Explain Task 1 – Part A.",
    "stop"
]

for message in test_messages:
    print(f"\n📝 消息: '{message}'")
    
    # 测试各个识别函数
    is_explain = service.is_explain_plan_request(message)
    is_stop = service.is_stop_request(message)
    is_why = service.is_why_plan_request(message)
    task_num, part_letter = service.parse_explain_task_part_request(message)
    
    print(f"   Explain plan: {'✅' if is_explain else '❌'}")
    print(f"   Stop: {'✅' if is_stop else '❌'}")
    print(f"   Why plan: {'✅' if is_why else '❌'}")
    print(f"   Task/Part: {task_num, part_letter if task_num and part_letter else '❌'}")

# 测试当前模式获取
print(f"\n🎯 当前模式: {service.get_current_mode(account.student_id)}")

# 测试实际的process_message - 完整流程
print("\n🧪 测试完整的explain plan流程:")

test_scenarios = [
    "Explain my plan",
    "Why did you give me this plan?", 
    "Explain Task 1 – Part A.",
    "Explain Task 99 – Part Z.",
    "stop",
    "Explain Task 1 – Part A."  # 验证退出后再触发
]

for i, message in enumerate(test_scenarios, 1):
    print(f"\n📝 场景 {i}: {message}")
    print(f"🎯 当前模式: {service.get_current_mode(account.student_id)}")
    
    try:
        result = service.process_message(account, message)
        
        if result.get('success'):
            ai_response = result.get('ai_response', {})
            content = ai_response.get('content', '')
            intent = ai_response.get('intent', '')
            
            print(f"✅ 处理成功")
            print(f"🎯 意图: {intent}")
            print(f"📄 回复: {content[:200]}...")
            print(f"🎯 新模式: {service.get_current_mode(account.student_id)}")
        else:
            print(f"❌ 处理失败: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 处理异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("-" * 60)