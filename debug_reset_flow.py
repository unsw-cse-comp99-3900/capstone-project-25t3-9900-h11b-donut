#!/usr/bin/env python3
"""
重置并重新测试练习流程
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from ai_chat.models import PracticeSetupState
from stu_accounts.models import StudentAccount

def reset_and_test():
    print("=== 重置并重新测试练习流程 ===")
    
    # 获取用户账户
    try:
        account = StudentAccount.objects.get(student_id='5215555')
        print(f"找到用户账户: {account.name}")
    except StudentAccount.DoesNotExist:
        print("用户账户不存在")
        return
    
    # 清除之前的练习状态
    PracticeSetupState.objects.filter(student_id='5215555').delete()
    print("已清除之前的练习状态")
    
    # 创建聊天服务实例
    chat_service = AIChatService()
    
    # 步骤1: 发送练习请求
    print("\n=== 步骤1: 发送练习请求 ===")
    result1 = chat_service.process_message(account, "I want to do some practice for COMP9417")
    print(f"AI回复: {result1.get('ai_response', {}).get('content', '')[:200]}...")
    
    # 步骤2: 选择课程
    print("\n=== 步骤2: 选择课程 ===")
    result2 = chat_service.process_message(account, "COMP9417")
    print(f"AI回复: {result2.get('ai_response', {}).get('content', '')[:200]}...")
    
    # 步骤3: 选择主题
    print("\n=== 步骤3: 选择主题 ===")
    result3 = chat_service.process_message(account, "goals")
    ai_content = result3.get('ai_response', {}).get('content', '')
    print(f"AI完整回复: {ai_content}")
    
    # 检查结果
    print("\n=== 检查结果 ===")
    if "I've generated" in ai_content:
        print("✅ 生成成功!")
        if "Start Practice Session" in ai_content:
            print("✅ 包含按钮!")
        else:
            print("❌ 没有按钮")
    elif "Sorry, I encountered an issue" in ai_content:
        print("❌ 生成失败!")
    elif "I'm now generating" in ai_content:
        print("⚠️ 只显示了生成中消息，没有实际生成")
    else:
        print("⚠️ 返回了意外结果")
    
    # 检查练习状态
    state = chat_service.get_practice_setup_state('5215555')
    print(f"当前练习状态: {state}")

if __name__ == "__main__":
    reset_and_test()