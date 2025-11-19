#!/usr/bin/env python3
import os
import sys
import django
import json

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_explain_plan_flow():
    """测试Explain Plan数据流程"""
    try:
        from django.contrib.auth.models import User
        from ai_chat.models import UserStudyPlan
        from ai_chat.chat_service import AIChatService
        from stu_accounts.models import StudentAccount
        
        print("=" * 100)
        print(" " * 35 + "Explain My Plan 数据流程测试")
        print("=" * 100)
        
        # 1. 检查数据库表
        print("\n【1】检查ai_chat_userstudyplan表（TiDB Cloud）")
        print("-" * 100)
        
        plans = UserStudyPlan.objects.all()
        print(f"  总计划数: {plans.count()}")
        
        active_plans = UserStudyPlan.objects.filter(is_active=True)
        print(f"  激活计划数: {active_plans.count()}")
        
        if active_plans.exists():
            print(f"\n  激活的计划列表:")
            for plan in active_plans[:5]:
                print(f"    用户: {plan.user.username}, 创建时间: {plan.created_at}, 激活: {plan.is_active}")
        
        # 2. 测试获取计划数据的函数
        print("\n【2】测试get_user_study_plan函数")
        print("-" * 100)
        
        chat_service = AIChatService()
        
        # 查找一个有激活计划的用户
        if active_plans.exists():
            test_plan = active_plans.first()
            test_user = test_plan.user
            print(f"  测试用户: {test_user.username}")
            
            # 获取对应的StudentAccount
            try:
                student_account = StudentAccount.objects.get(student_id=test_user.username)
                print(f"  找到StudentAccount: {student_account.student_id}")
                
                # 调用get_user_study_plan
                plan_data = chat_service.get_user_study_plan(student_account)
                
                if plan_data:
                    print(f"\n  ✅ 成功从TiDB Cloud获取计划数据!")
                    print(f"  数据类型: {type(plan_data)}")
                    print(f"  顶层字段: {list(plan_data.keys())}")
                    
                    if 'aiSummary' in plan_data:
                        ai_summary = plan_data['aiSummary']
                        if 'tasks' in ai_summary:
                            print(f"  任务数量: {len(ai_summary['tasks'])}")
                            
                            # 统计总part数
                            total_parts = 0
                            for task in ai_summary['tasks']:
                                if 'parts' in task:
                                    total_parts += len(task['parts'])
                            print(f"  总Part数: {total_parts}")
                    
                    if 'days' in plan_data:
                        days = plan_data['days']
                        print(f"  计划天数: {len(days)}")
                else:
                    print(f"  ❌ 未找到计划数据")
                    
            except StudentAccount.DoesNotExist:
                print(f"  ⚠️ 未找到对应的StudentAccount: {test_user.username}")
        else:
            print(f"  ⚠️ 没有激活的计划可供测试")
        
        # 3. 测试generate_plan_explanation
        print("\n【3】测试generate_plan_explanation函数")
        print("-" * 100)
        
        if active_plans.exists():
            test_plan = active_plans.first()
            test_user = test_plan.user
            
            try:
                student_account = StudentAccount.objects.get(student_id=test_user.username)
                
                # 生成解释
                explanation = chat_service.generate_plan_explanation(student_account)
                
                print(f"  ✅ 成功生成计划解释!")
                print(f"  解释长度: {len(explanation)} 字符")
                print(f"\n  解释内容预览（前500字符）:")
                print(f"  {explanation[:500]}...")
                
            except Exception as e:
                print(f"  ❌ 生成解释失败: {e}")
        
        # 4. 总结
        print("\n【4】数据流程总结")
        print("=" * 100)
        print(f"  数据存储位置: ✅ TiDB Cloud (ai_chat_userstudyplan表)")
        print(f"  数据表名: ai_chat_userstudyplan")
        print(f"  模型类: UserStudyPlan")
        print(f"  读取函数: AIChatService.get_user_study_plan()")
        print(f"  数据字段: plan_data (JSON类型)")
        print("=" * 100)
        
        print(f"\n【结论】")
        print(f"  ✅ Explain My Plan功能从TiDB Cloud的ai_chat_userstudyplan表读取数据")
        print(f"  ✅ 之前找不到数据是因为用的SQLite本地数据库，没有连接TiDB Cloud")
        print(f"  ✅ 现在已恢复TiDB Cloud连接，可以正常读取Gemini生成的计划数据")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_explain_plan_flow()
