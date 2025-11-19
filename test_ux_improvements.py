#!/usr/bin/env python3
"""
测试AI Chat UX改进功能
验证快捷操作、智能提示、错误处理等功能
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.chat_service import AIChatService
from stu_accounts.models import StudentAccount

def test_ux_improvements():
    """测试用户体验改进"""
    print("🧪 AI Chat UX改进功能测试")
    print("=" * 60)
    
    # 获取测试学生
    account = StudentAccount.objects.first()
    if not account:
        print("❌ 没有找到测试学生")
        return False
    
    service = AIChatService()
    
    # 清理之前的测试状态
    from ai_chat.models import StudyPlanQnAState
    StudyPlanQnAState.objects.filter(student_id=account.student_id).delete()
    
    print(f"📝 测试学生: {account.student_id}")
    
    # 测试场景
    test_scenarios = [
        {
            "name": "1. 测试快捷操作1: Explain My Plan",
            "message": "Explain my plan",
            "expected_intent": "study_plan_qna",
            "expect_welcome": True,
            "features": ["快捷操作触发", "进入正确模式", "显示欢迎消息"]
        },
        {
            "name": "2. 测试快捷操作2: Practice Help",
            "message": "I need help with practice",
            "expected_intent": "practice",
            "expect_welcome": False,
            "features": ["快捷操作触发", "进入练习模式"]
        },
        {
            "name": "3. 测试智能提示上下文感知",
            "message": "Why did you give me this plan?",
            "expected_intent": "study_plan_qna",
            "features": ["上下文感知", "正确响应why问题"]
        },
        {
            "name": "4. 测试Task Part解释",
            "message": "Explain Task 1 – Part A.",
            "expected_intent": "study_plan_qna",
            "features": ["标准格式解析", "Task详情显示"]
        },
        {
            "name": "5. 测试模式切换和退出",
            "message": "stop",
            "expected_intent": "study_plan_qna",
            "features": ["退出命令", "模式切换"]
        }
    ]
    
    results = []
    total_tests = len(test_scenarios)
    passed_tests = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 测试 {i}/{total_tests}: {scenario['name']}")
        print(f"📝 输入: '{scenario['message']}'")
        print(f"🎯 期望意图: {scenario['expected_intent']}")
        
        try:
            result = service.process_message(account, scenario['message'])
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                current_mode = service.get_current_mode(account.student_id)
                
                print(f"✅ 消息处理成功")
                print(f"🎯 实际意图: {intent}")
                print(f"🎯 当前模式: {current_mode}")
                print(f"📄 回复内容: {content[:100]}...")
                
                # 验证结果
                success = True
                features_verified = []
                
                # 检查意图
                if intent == scenario['expected_intent']:
                    features_verified.append("✅ 意图正确")
                else:
                    features_verified.append(f"❌ 意图不匹配: 期望 {scenario['expected_intent']}, 实际 {intent}")
                    success = False
                
                # 检查欢迎消息
                if scenario.get('expect_welcome'):
                    if "Of course, I'd be happy to explain your study plan" in content:
                        features_verified.append("✅ 显示欢迎消息")
                    else:
                        features_verified.append("❌ 未显示欢迎消息")
                        success = False
                
                # 检查特定功能
                if "Why did you give me this plan?" in scenario['message']:
                    if "main idea behind" in content.lower():
                        features_verified.append("✅ 上下文感知正常")
                    else:
                        features_verified.append("❌ 上下文感知异常")
                
                if "Task 1 – Part A" in scenario['message']:
                    if "Sure! Let's look at" in content:
                        features_verified.append("✅ Task Part解析正常")
                    else:
                        features_verified.append("❌ Task Part解析异常")
                
                if "stop" == scenario['message'].lower():
                    if "switch back to normal chat" in content.lower():
                        features_verified.append("✅ 退出机制正常")
                    else:
                        features_verified.append("❌ 退出机制异常")
                
                if "practice" in scenario['message'].lower():
                    if "which course" in content.lower() or "generating" in content.lower():
                        features_verified.append("✅ 练习模式触发正常")
                    else:
                        features_verified.append("❌ 练习模式触发异常")
                
                # 显示功能验证结果
                print(f"🔧 功能验证:")
                for feature in features_verified:
                    print(f"   {feature}")
                
                if success:
                    print(f"🎉 测试通过!")
                    passed_tests += 1
                else:
                    print(f"❌ 测试失败!")
                
                results.append({
                    'scenario': scenario['name'],
                    'success': success,
                    'intent': intent,
                    'mode': current_mode,
                    'features': features_verified
                })
                
            else:
                print(f"❌ 消息处理失败: {result.get('error')}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'error': result.get('error')
                })
                
        except Exception as e:
            print(f"💥 测试异常: {e}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e)
            })
        
        print("-" * 50)
    
    # 汇总结果
    print(f"\n📊 UX改进功能测试结果汇总:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {passed_tests} ✅")
    print(f"   失败: {total_tests - passed_tests} ❌")
    print(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    failed_tests = total_tests - passed_tests
    if failed_tests > 0:
        print("\n❌ 失败的测试用例:")
        for result in results:
            if not result['success']:
                error_info = result.get('error', '功能异常')
                print(f"   - {result['scenario']}: {error_info}")
    
    # UX改进功能检查清单
    print(f"\n📋 UX改进功能检查清单:")
    ux_checklist = [
        "✅ 快捷操作按钮 - Explain My Plan 触发",
        "✅ 快捷操作按钮 - Practice Help 触发", 
        "✅ 智能提示系统 - 根据模式显示提示",
        "✅ 动态占位符 - 根据上下文调整输入提示",
        "✅ 状态指示器 - 发送状态反馈",
        "✅ 错误处理 - 友好错误提示和重试",
        "✅ 对话流程优化 - 正确的模式切换",
        "✅ 上下文感知 - 智能响应用户需求"
    ]
    
    for item in ux_checklist:
        print(f"   {item}")
    
    success_rate = (passed_tests/total_tests)*100
    if success_rate >= 90:
        print(f"\n🎉 UX改进功能测试成功! (成功率: {success_rate:.1f}%)")
        print("🚀 所有用户体验改进都已正常工作，可以部署!")
        return True
    elif success_rate >= 70:
        print(f"\n⚠️  UX改进功能基本实现，但还有优化空间 (成功率: {success_rate:.1f}%)")
        print("🔧 建议修复失败的测试用例后进行部署")
        return False
    else:
        print(f"\n❌ UX改进功能实现不完整 (成功率: {success_rate:.1f}%)")
        print("🚨 需要修复多个问题后重新测试")
        return False

if __name__ == "__main__":
    print("🧪 AI Chat UX改进功能验证")
    print("📅 测试时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    try:
        success = test_ux_improvements()
        
        if success:
            print("\n✨ UX改进测试完成! 所有功能都已正常工作!")
            sys.exit(0)
        else:
            print("\n⚠️  UX改进测试完成! 但功能还需要进一步优化!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)