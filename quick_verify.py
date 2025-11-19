#!/usr/bin/env python3
"""
快速验证 - 检查所有学生的计划状态
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
from ai_chat.models import UserStudyPlan
from django.contrib.auth.models import User

def quick_verify():
    """快速验证所有学生账户的plan状态"""
    print("⚡ 快速验证学生计划状态")
    print("=" * 50)
    
    # 获取所有有计划的学生
    service = AIChatService()
    
    print("👥 检查所有学生的计划状态:")
    print("-" * 50)
    
    accounts = StudentAccount.objects.all()[:10]  # 显示前10个
    plan_count = 0
    
    for account in accounts:
        try:
            # 获取Django User
            user, _ = User.objects.get_or_create(
                username=account.student_id,
                defaults={'email': account.email or f'{account.student_id}@temp.com'}
            )
            
            # 检查计划
            plan_data = service.get_user_study_plan(account)
            
            if plan_data:
                plan_count += 1
                print(f"✅ {account.student_id}: 有活跃计划")
                print(f"   姓名: {account.name}")
                print(f"   邮箱: {account.email}")
                
                # 测试why plan响应
                result = service.process_message(account, "Why did you give me this plan?")
                if result.get('success'):
                    content = result.get('ai_response', {}).get('content', '')
                    if "I don't see an active study plan" in content:
                        print(f"   ❌ 仍然返回错误!")
                        print(f"   错误回复: {content[:100]}...")
                    elif "Great question" in content or "really good question" in content:
                        print(f"   ✅ 正确返回计划解释!")
                    else:
                        print(f"   ⚠️ 未知回复类型")
                else:
                    print(f"   ❌ 处理失败")
            else:
                print(f"❌ {account.student_id}: 无活跃计划")
                
            print()
            
        except Exception as e:
            print(f"💥 {account.student_id}: 检查出错 - {e}")
    
    print("-" * 50)
    print(f"📊 汇总结果:")
    print(f"   检查学生数: {len(accounts)}")
    print(f"   有计划学生数: {plan_count}")
    print(f"   无计划学生数: {len(accounts) - plan_count}")
    
    if plan_count > 0:
        print(f"\n✅ 找到 {plan_count} 个学生有活跃计划!")
        print("🎯 Explain My Plan 功能应该对正常工作的学生")
        print("💡 如果你仍然看到错误，请检查:")
        print("   1. 是否使用了正确的学生账户登录")
        print("   2. 是否清除了浏览器缓存")
        print("   3. 是否在正确的会话中测试")
    else:
        print(f"\n❌ 没有找到任何有计划的学生!")
        print("🔧 需要先为一些学生生成学习计划")

if __name__ == "__main__":
    quick_verify()