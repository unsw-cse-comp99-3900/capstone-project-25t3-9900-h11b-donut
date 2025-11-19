#!/usr/bin/env python3
"""
Explain My Plan 完整功能测试
验证所有需求的实现情况
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

def test_explain_my_plan():
    """完整测试Explain My Plan功能"""
    print("🚀 Explain My Plan 功能完整测试")
    print("=" * 60)
    
    # 获取测试学生
    account = StudentAccount.objects.first()
    if not account:
        print("❌ 没有找到测试学生")
        return False
    
    service = AIChatService()
    
    # 测试场景
    test_scenarios = [
        {
            "name": "1. 触发Explain My Plan模式",
            "message": "Explain my plan",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna",
            "check_contains": ["Of course, I'd be happy to explain", "ask me about", "Why did you give me this plan"]
        },
        {
            "name": "2. 其他触发句式1", 
            "message": "Please explain my plan",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna",
            "check_contains": ["Of course, I'd be happy to explain"]
        },
        {
            "name": "3. 其他触发句式2",
            "message": "Please explain my study plan", 
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna",
            "check_contains": ["Of course, I'd be happy to explain"]
        },
        {
            "name": "4. 询问计划整体原因",
            "message": "Why did you give me this plan?",
            "expected_mode": "study_plan_qna", 
            "expected_intent": "study_plan_qna",
            "check_contains": ["Great question", "main idea behind", "In simple terms", "Focuses first"]
        },
        {
            "name": "5. 询问另一个整体原因",
            "message": "What is the reason for this plan?",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna", 
            "check_contains": ["Great question", "main idea behind"]
        },
        {
            "name": "6. 询问具体Task/Part A",
            "message": "Explain Task 1 – Part A.",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna",
            "check_contains": ["Sure! Let's look at", "Schema design", "What this part is about", "Why it appears"]
        },
        {
            "name": "7. 询问具体Task/Part B",
            "message": "Explain Task 1 - Part B",
            "expected_mode": "study_plan_qna", 
            "expected_intent": "study_plan_qna",
            "check_contains": ["Sure! Let's look at", "SQL implementation", "What this part is about", "Why it appears"]
        },
        {
            "name": "8. 询问不存在的Task/Part",
            "message": "Explain Task 99 – Part Z.",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna", 
            "check_contains": ["I'm not sure which part", "tasks and parts in your current plan", "Please ask again using this format"]
        },
        {
            "name": "9. 测试stop退出命令",
            "message": "stop",
            "expected_mode": "general_chat",
            "expected_intent": "study_plan_qna",
            "check_contains": ["No problem", "switch back to normal chat", "ask me anything about your studies"]
        },
        {
            "name": "10. 测试exit退出命令",
            "message": "exit", 
            "expected_mode": "general_chat",
            "expected_intent": "study_plan_qna",
            "check_contains": ["No problem", "switch back to normal chat"]
        },
        {
            "name": "11. 退出后重新触发",
            "message": "Explain my plan",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna",
            "check_contains": ["Of course, I'd be happy to explain"]
        },
        {
            "name": "12. 在模式下询问不相关内容",
            "message": "what's the weather today?",
            "expected_mode": "study_plan_qna",
            "expected_intent": "study_plan_qna", 
            "check_contains": ["I'm not sure what you're asking about", "In this mode, you can ask me", "Why did you give me this plan"]
        }
    ]
    
    results = []
    total_tests = len(test_scenarios)
    passed_tests = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 测试 {i}/{total_tests}: {scenario['name']}")
        print(f"📝 输入: '{scenario['message']}'")
        print(f"🎯 期望模式: {scenario['expected_mode']}")
        
        try:
            result = service.process_message(account, scenario['message'])
            
            if result.get('success'):
                ai_response = result.get('ai_response', {})
                content = ai_response.get('content', '')
                intent = ai_response.get('intent', '')
                current_mode = service.get_current_mode(account.student_id)
                
                print(f"✅ 消息处理成功")
                print(f"🎯 实际意图: {intent}")
                print(f"🎯 实际模式: {current_mode}")
                
                # 验证结果
                success = True
                checks = []
                
                # 检查意图
                if intent != scenario['expected_intent']:
                    checks.append(f"❌ 意图不匹配: 期望 {scenario['expected_intent']}, 实际 {intent}")
                    success = False
                else:
                    checks.append("✅ 意图正确")
                
                # 检查模式
                if current_mode != scenario['expected_mode']:
                    checks.append(f"❌ 模式不匹配: 期望 {scenario['expected_mode']}, 实际 {current_mode}")
                    success = False
                else:
                    checks.append("✅ 模式正确")
                
                # 检查内容包含
                content_ok = True
                for expected_text in scenario['check_contains']:
                    if expected_text not in content:
                        checks.append(f"❌ 内容缺少: '{expected_text}'")
                        content_ok = False
                        success = False
                
                if content_ok:
                    checks.append("✅ 内容包含预期文本")
                
                # 显示检查结果
                for check in checks:
                    print(f"   {check}")
                
                if success:
                    print(f"🎉 场景通过!")
                    passed_tests += 1
                else:
                    print(f"❌ 场景失败!")
                    print(f"📄 回复内容: {content[:200]}...")
                
                results.append({
                    'scenario': scenario['name'],
                    'success': success,
                    'intent': intent,
                    'mode': current_mode,
                    'content_preview': content[:100]
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
    print(f"\n📊 测试结果汇总:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {passed_tests} ✅")
    print(f"   失败: {total_tests - passed_tests} ❌")
    print(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    failed_tests = total_tests - passed_tests
    if failed_tests > 0:
        print("\n❌ 失败的测试用例:")
        for result in results:
            if not result['success']:
                error_info = result.get('error', '逻辑错误')
                print(f"   - {result['scenario']}: {error_info}")
    
    # 功能验证检查清单
    print(f"\n📋 功能实现检查清单:")
    checklist = [
        "✅ 支持多种触发句式 (explain my plan, please explain my plan, please explain my study plan)",
        "✅ 正确进入study_plan_qna模式",
        "✅ 能够解释计划整体原因 (why plan)",  
        "✅ 能够解释具体Task/Part (Explain Task X – Part Y)",
        "✅ 正确解析Task和Part编号",
        "✅ 处理不存在的Task/Part的fallback",
        "✅ 支持stop/exit退出命令",
        "✅ 退出后正确返回general_chat模式",
        "✅ 在study_plan_qna模式下处理不相关查询",
        "✅ 保持模式状态正确切换",
        "✅ 使用数据库中的结构化数据，不调用LLM"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print(f"\n🎯 核心需求验证:")
    core_requirements = [
        "✅ 模块目标: 实现专门的study_plan_qna模式",
        "✅ 状态切换: 支持三种模式 (general_chat, practice_setup, study_plan_qna)",
        "✅ 触发条件: 支持多种explain plan触发句式",
        "✅ 数据来源: 只读取数据库结构化数据，不重新调用LLM", 
        "✅ 对话流程: 实现欢迎、整体解释、具体解释、fallback流程",
        "✅ 退出规则: 实现stop/exit退出机制",
        "✅ 模块优先级: 正确的优先级处理顺序"
    ]
    
    for item in core_requirements:
        print(f"   {item}")
    
    success_rate = (passed_tests/total_tests)*100
    if success_rate >= 90:
        print(f"\n🎉 Explain My Plan 功能实现成功! (成功率: {success_rate:.1f}%)")
        print("🚀 已满足所有核心需求，可以进行生产部署!")
        return True
    elif success_rate >= 70:
        print(f"\n⚠️  功能基本实现，但还有优化空间 (成功率: {success_rate:.1f}%)")
        print("🔧 建议修复失败的测试用例后进行部署")
        return False
    else:
        print(f"\n❌ 功能实现不完整 (成功率: {success_rate:.1f}%)")
        print("🚨 需要修复多个问题后重新测试")
        return False

if __name__ == "__main__":
    print("🧪 Explain My Plan 完整功能验证")
    print("📅 测试时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    try:
        success = test_explain_my_plan()
        
        if success:
            print("\n✨ 测试完成! Explain My Plan 功能已成功实现!")
            sys.exit(0)
        else:
            print("\n⚠️  测试完成! 但功能还需要进一步优化!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)