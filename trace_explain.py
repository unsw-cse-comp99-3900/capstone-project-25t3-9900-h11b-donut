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

account = StudentAccount.objects.first()
service = AIChatService()

print("🔍 追踪explain my plan流程的详细步骤:")

# 先进入explain my plan模式
message = "Explain my plan"
print(f"\n📝 步骤1: {message}")
print(f"🎯 进入前模式: {service.get_current_mode(account.student_id)}")

result = service.process_message(account, message)
print(f"✅ 处理结果: {result.get('success')}")
if result.get('success'):
    ai_response = result.get('ai_response', {})
    print(f"🎯 意图: {ai_response.get('intent')}")
print(f"🎯 进入后模式: {service.get_current_mode(account.student_id)}")

# 测试在模式下的消息
test_message = "Explain Task 1 – Part A."
print(f"\n📝 步骤2: {test_message}")
print(f"🎯 当前模式: {service.get_current_mode(account.student_id)}")

# 手动测试各个识别函数
is_explain = service.is_explain_plan_request(test_message)
is_stop = service.is_stop_request(test_message)
is_why = service.is_why_plan_request(test_message)
task_num, part_letter = service.parse_explain_task_part_request(test_message)

print(f"🔍 识别结果:")
print(f"   is_explain_plan_request: {is_explain}")
print(f"   is_stop_request: {is_stop}")
print(f"   is_why_plan_request: {is_why}")
print(f"   parse_explain_task_part_request: {task_num, part_letter}")

# 手动调用handle_study_plan_qna_mode
print(f"\n🧪 手动调用handle_study_plan_qna_mode:")
response = service.handle_study_plan_qna_mode(account, test_message)
print(f"📄 回复: {response[:100] if response else 'None'}...")

# 通过process_message测试
print(f"\n🧪 通过process_message测试:")
result = service.process_message(account, test_message)
print(f"✅ 处理结果: {result.get('success')}")
if result.get('success'):
    ai_response = result.get('ai_response', {})
    print(f"🎯 意图: {ai_response.get('intent')}")
    print(f"📄 回复: {ai_response.get('content', '')[:100] if ai_response.get('content') else 'None'}...")
print(f"🎯 最终模式: {service.get_current_mode(account.student_id)}")