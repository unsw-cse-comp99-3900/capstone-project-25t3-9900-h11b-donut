#!/usr/bin/env python3
"""测试Why Plan解释功能"""
import os
import sys
import django

sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from stu_accounts.models import StudentAccount
from ai_chat.chat_service import AIChatService

# 获取z1234567账号
account = StudentAccount.objects.get(student_id='z1234567')

# 创建服务实例
service = AIChatService()

# 获取计划数据
plan_data = service.get_user_study_plan(account)

if plan_data:
    # 生成Why Plan解释
    explanation = service.generate_why_plan_explanation(plan_data)
    
    print("="*80)
    print("🔍 测试 'Why did you give me this plan?' 的回复")
    print("="*80)
    print("\n返回的HTML内容:")
    print(explanation)
    print("\n" + "="*80)
    
    # 检查是否包含explanation
    if 'Why this breakdown:' in explanation:
        print("✅ 成功包含任务解释 (explanation字段)")
    else:
        print("❌ 未包含任务解释")
    
    if 'COMP9331' in explanation or 'COMP9417' in explanation or 'COMP9900' in explanation:
        print("✅ 包含具体任务信息")
    else:
        print("❌ 未包含具体任务信息")
    
    # 检查是否还有通用文本
    if 'Focuses first on the tasks that are due the soonest' in explanation:
        print("⚠️ 仍包含旧的通用文本")
    else:
        print("✅ 已移除旧的通用文本")
else:
    print("❌ 未找到计划数据")
