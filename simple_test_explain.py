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
from django.contrib.auth.models import User

# 使用现有的学生账户或创建一个简单的
try:
    # 先尝试获取现有学生
    existing_student = StudentAccount.objects.first()
    if existing_student:
        account = existing_student
        print(f"✅ 使用现有学生: {account.student_id}")
    else:
        print("❌ 没有找到现有学生账户")
        sys.exit(1)
        
    # 创建AI Chat服务
    service = AIChatService()
    
    # 测试explain my plan功能
    print("\n🧪 测试 Explain My Plan 功能")
    
    # 测试消息
    test_messages = [
        "Explain my plan",
        "Please explain my study plan", 
        "Why did you give me this plan?",
        "Explain Task 1 – Part A.",
        "stop"
    ]
    
    for message in test_messages:
        print(f"\n📝 测试消息: {message}")
        result = service.process_message(account, message)
        
        if result.get('success'):
            ai_response = result.get('ai_response', {})
            content = ai_response.get('content', '')
            intent = ai_response.get('intent', '')
            
            print(f"✅ 成功处理")
            print(f"🎯 意图: {intent}")
            print(f"📄 回复: {content[:150]}...")
        else:
            print(f"❌ 处理失败: {result.get('error')}")
    
    print("\n🎉 测试完成!")
    
except Exception as e:
    print(f"💥 错误: {e}")
    import traceback
    traceback.print_exc()