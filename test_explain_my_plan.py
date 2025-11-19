#!/usr/bin/env python3
"""
Explain My Plan 功能测试脚本
测试AI Chat模块的study_plan_qna模式功能

使用方法:
python test_explain_my_plan.py
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount
from django.contrib.auth.models import User

def create_test_student():
    """创建测试学生账户"""
    student_id = "test_explain_plan"
    try:
        # 创建Django User
        user, created = User.objects.get_or_create(
            username=student_id,
            defaults={
                'email': f'{student_id}@test.com',
                'first_name': 'Test',
                'last_name': 'Student'
            }
        )
        
        # 创建StudentAccount
        account, created = StudentAccount.objects.get_or_create(
            student_id=student_id,
            defaults={
                'name': 'Test Student',
                'email': f'{student_id}@test.com',
                'password_hash': 'test_hash_12345678901234567890123456789012345678901234567890'
            }
        )
        
        print(f"✅ 创建测试学生: {student_id}")
        return account
        
    except Exception as e:
        print(f"❌ 创建测试学生失败: {e}")
        return None

def create_test_study_plan(account):
    """创建测试学习计划"""
    try:
        # 先创建临时User对象
        user, _ = User.objects.get_or_create(
            username=account.student_id,
            defaults={'email': account.email or f'{account.student_id}@test.com'}
        )
        
        from ai_chat.models import UserStudyPlan
        
        # 将之前的计划设为非活跃
        UserStudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # 创建测试计划数据
        test_plan_data = {
            "overall_reason": "This plan is designed to help you complete your assignments efficiently while balancing your workload. It prioritizes tasks with earlier deadlines and allocates sufficient time for each part.",
            "aiSummary": {
                "tasks": [
                    {
                        "taskTitle": "Database Design Assignment",
                        "parts": [
                            {
                                "label": "Schema design",
                                "detail": "Design the database schema with proper normalization, relationships, and constraints. Focus on creating tables for users, products, and orders.",
                                "why_in_plan": "This is the foundation of your database assignment and needs to be completed first before implementing queries and reports."
                            },
                            {
                                "label": "SQL implementation", 
                                "detail": "Implement the designed schema using SQL DDL statements, including tables, indexes, constraints, and relationships.",
                                "why_in_plan": "After designing the schema, you need to create it in the database system using proper SQL syntax."
                            }
                        ],
                        "totalMinutes": 180
                    },
                    {
                        "taskTitle": "Algorithm Analysis Project",
                        "parts": [
                            {
                                "label": "Research phase",
                                "detail": "Research and understand the algorithms to be analyzed, including their time complexity, space complexity, and use cases.",
                                "why_in_plan": "Research is crucial as it forms the theoretical foundation for your analysis and implementation."
                            },
                            {
                                "label": "Implementation",
                                "detail": "Implement the algorithms in your preferred programming language with proper documentation and testing.",
                                "why_in_plan": "Implementation allows you to practically apply your theoretical understanding and validate your complexity analysis."
                            }
                        ],
                        "totalMinutes": 240
                    }
                ]
            }
        }
        
        # 保存测试计划
        UserStudyPlan.objects.create(
            user=user,
            plan_data=test_plan_data,
            is_active=True
        )
        
        print(f"✅ 创建测试学习计划")
        return test_plan_data
        
    except Exception as e:
        print(f"❌ 创建测试学习计划失败: {e}")
        return None

def test_explain_plan_functionality():
    """测试Explain My Plan功能"""
    print("🚀 开始测试 Explain My Plan 功能")
    print("=" * 50)
    
    # 创建测试数据
    account = create_test_student()
    if not account:
        return False
    
    plan_data = create_test_study_plan(account)
    if not plan_data:
        return False
    
    # 创建AI Chat服务实例
    service = AIChatService()
    
    # 测试用例
    test_cases = [
        {
            "name": "触发 Explain My Plan 模式",
            "message": "Explain my plan",
            "expected_intent": "study_plan_qna",
            "description": "应该进入study_plan_qna模式并显示欢迎消息"
        },
        {
            "name": "询问计划整体原因",
            "message": "Why did you give me this plan?",
            "expected_intent": "study_plan_qna", 
            "description": "应该显示计划的整体原因"
        },
        {
            "name": "询问具体Task/Part",
            "message": "Explain Task 1 – Part A.",
            "expected_intent": "study_plan_qna",
            "description": "应该显示Task 1 Part A的详细信息"
        },
        {
            "name": "询问另一个Task/Part",
            "message": "Explain Task 2 - Part B",
            "expected_intent": "study_plan_qna",
            "description": "应该显示Task 2 Part B的详细信息"
        },
        {
            "name": "测试不存在的Task/Part",
            "message": "Explain Task 99 – Part Z.",
            "expected_intent": "study_plan_qna",
            "description": "应该显示错误提示和可用任务列表"
        },
        {
            "name": "测试退出命令",
            "message": "stop",
            "expected_intent": "study_plan_qna",
            "description": "应该退出study_plan_qna模式"
        },
        {
            "name": "测试其他触发句式",
            "message": "Please explain my study plan",
            "expected_intent": "study_plan_qna",
            "description": "应该识别其他explain plan触发句式"
        }
    ]
    
    print(f"📋 准备执行 {len(test_cases)} 个测试用例")
    print()
    
    # 执行测试
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 测试用例 {i}: {test_case['name']}")
        print(f"📝 输入消息: {test_case['message']}")
        print(f"📋 描述: {test_case['description']}")
        
        try:
            # 处理消息
            result = service.process_message(account, test_case['message'])
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                
                print(f"✅ 消息处理成功")
                print(f"🎯 检测意图: {intent}")
                print(f"📄 AI回复预览: {content[:100]}...")
                
                # 验证结果
                success = True
                if 'expected_intent' in test_case:
                    if intent != test_case['expected_intent']:
                        print(f"⚠️  意图不匹配: 期望 {test_case['expected_intent']}, 实际 {intent}")
                        success = False
                
                results.append({
                    'test_case': test_case['name'],
                    'success': success,
                    'intent': intent,
                    'message': test_case['message'],
                    'response_preview': content[:100]
                })
                
            else:
                print(f"❌ 消息处理失败: {result.get('error', 'Unknown error')}")
                results.append({
                    'test_case': test_case['name'],
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'message': test_case['message']
                })
                
        except Exception as e:
            print(f"💥 测试异常: {e}")
            results.append({
                'test_case': test_case['name'],
                'success': False,
                'error': str(e),
                'message': test_case['message']
            })
        
        print("-" * 50)
    
    # 汇总结果
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"📊 测试结果汇总:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {passed_tests} ✅")
    print(f"   失败: {failed_tests} ❌")
    print(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ 失败的测试用例:")
        for result in results:
            if not result['success']:
                print(f"   - {result['test_case']}: {result.get('error', 'Intent mismatch')}")
    
    print("\n🎉 Explain My Plan 功能测试完成!")
    return failed_tests == 0

def test_pattern_matching():
    """测试模式匹配功能"""
    print("\n🔍 测试模式匹配功能")
    print("=" * 30)
    
    service = AIChatService()
    
    test_messages = [
        ("Explain my plan", True),
        ("Please explain my plan", True),
        ("Please explain my study plan", True),
        ("tell me about my plan", False),
        ("why is my plan like this", False),
        ("What is the reason for this plan", False),
        ("Explain Task 1 – Part A.", True),
        ("Explain Task 2 - Part B", True),
        ("stop", True),
        ("exit", True),
        ("back", True),
    ]
    
    print("测试各种消息格式的识别:")
    for message, expected in test_messages:
        # 测试explain plan识别
        is_explain = service.is_explain_plan_request(message)
        is_stop = service.is_stop_request(message)
        is_task_part = service.is_task_part_request(message) if hasattr(service, 'is_task_part_request') else False
        
        print(f"  '{message}'")
        print(f"    Explain: {'✅' if is_explain else '❌'}")
        print(f"    Stop: {'✅' if is_stop else '❌'}")
        print(f"    Task/Part: {'✅' if is_task_part else '❌'}")
        print()

if __name__ == "__main__":
    print("🧪 Explain My Plan 功能测试工具")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = test_explain_plan_functionality()
        test_pattern_matching()
        
        if success:
            print("\n🎯 所有核心功能测试通过!")
            sys.exit(0)
        else:
            print("\n⚠️  部分测试失败，请检查实现")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)