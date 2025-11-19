#!/usr/bin/env python3
"""直接查看数据库中的原始JSON数据"""
import os
import sys
import django

sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth.models import User
from stu_accounts.models import StudentAccount
from ai_chat.models import UserStudyPlan
import json

account = StudentAccount.objects.get(student_id='z1234567')
user = User.objects.get(username=account.student_id)

latest_plan = UserStudyPlan.objects.filter(user=user, is_active=True).first()

if latest_plan:
    plan_data = latest_plan.plan_data
    
    print("="*80)
    print("🔍 数据类型:", type(plan_data))
    print("="*80)
    
    # 如果是字典,直接打印
    if isinstance(plan_data, dict):
        print("\n📊 完整JSON数据 (格式化):")
        print(json.dumps(plan_data, indent=2, ensure_ascii=False))
    else:
        # 如果是字符串,先解析再打印
        print("\n📊 完整JSON数据 (格式化):")
        parsed = json.loads(plan_data)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
