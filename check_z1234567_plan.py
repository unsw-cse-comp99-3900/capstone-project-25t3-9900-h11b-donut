#!/usr/bin/env python3
"""检查z1234567用户的计划数据"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.db import connection
from stu_accounts.models import StudentAccount
from plans.models import StudyPlan
from ai_chat.models import UserStudyPlan
import json
from datetime import datetime

def check_z1234567_plans():
    print("="*80)
    print("🔍 检查 z1234567 用户的计划数据")
    print("="*80)
    
    try:
        # 1. 确认用户存在
        account = StudentAccount.objects.get(student_id='z1234567')
        print(f"\n✅ 用户信息:")
        print(f"   学生ID: {account.student_id}")
        print(f"   姓名: {account.name}")
        print(f"   邮箱: {account.email}")
        
        # 2. 检查 study_plan 表（前端用的表）
        print(f"\n{'='*80}")
        print("📋 study_plan 表 (前端My Plan页面用):")
        print("="*80)
        
        study_plans = StudyPlan.objects.filter(student_id=account.student_id).order_by('-created_at')
        print(f"   总计划数: {study_plans.count()}")
        
        if study_plans.exists():
            latest_plan = study_plans.first()
            print(f"\n   📌 最新计划:")
            print(f"      计划ID: {latest_plan.id}")
            print(f"      周开始日期: {latest_plan.week_start_date}")
            print(f"      创建时间: {latest_plan.created_at}")
            print(f"      数据来源: {latest_plan.source}")
            print(f"      周偏移: {latest_plan.week_offset}")
            
            # 查询关联的计划项
            from plans.models import StudyPlanItem
            plan_items = StudyPlanItem.objects.filter(plan=latest_plan)
            print(f"\n   📊 计划项统计:")
            print(f"      总计划项数: {plan_items.count()}")
            
            if plan_items.exists():
                # 统计课程
                courses = plan_items.values('course_code').distinct()
                print(f"      涉及课程数: {courses.count()}")
                for course in courses:
                    course_items = plan_items.filter(course_code=course['course_code'])
                    print(f"         {course['course_code']}: {course_items.count()} 项")
                
                # 统计完成情况
                completed_count = plan_items.filter(completed=True).count()
                print(f"      已完成: {completed_count}/{plan_items.count()}")
                
                # 显示几个示例
                print(f"\n   📄 计划项示例 (前5条):")
                for item in plan_items[:5]:
                    print(f"      - {item.course_code} | {item.scheduled_date} | {item.minutes}分钟 | {item.part_title}")
            
            # 检查meta字段（可能包含AI生成的原始数据）
            if latest_plan.meta:
                print(f"\n   📋 Meta数据:")
                print(f"      类型: {type(latest_plan.meta)}")
                if isinstance(latest_plan.meta, dict):
                    print(f"      字段: {list(latest_plan.meta.keys())}")
                    # 显示部分内容
                    meta_str = json.dumps(latest_plan.meta, indent=2, ensure_ascii=False)
                    meta_lines = meta_str.split('\n')[:30]
                    for line in meta_lines:
                        print(f"      {line}")
                    if len(meta_str.split('\n')) > 30:
                        print(f"      ... (还有更多)")
        else:
            print("   ⚠️ 没有找到study_plan记录")
        
        # 3. 检查 ai_chat_userstudyplan 表（AI Chat用的表）
        print(f"\n{'='*80}")
        print("🤖 ai_chat_userstudyplan 表 (AI Chat Explain My Plan用):")
        print("="*80)
        
        # 需要通过student_id找到User对象
        from django.contrib.auth.models import User
        try:
            # student_id可能被用作username
            user = User.objects.get(username=account.student_id)
            
            ai_plans = UserStudyPlan.objects.filter(user=user).order_by('-created_at')
            print(f"   总计划数: {ai_plans.count()}")
            print(f"   激活计划数: {ai_plans.filter(is_active=True).count()}")
            
            if ai_plans.exists():
                latest_ai_plan = ai_plans.first()
                print(f"\n   📌 最新AI计划:")
                print(f"      计划ID: {latest_ai_plan.id}")
                print(f"      创建时间: {latest_ai_plan.created_at}")
                print(f"      是否激活: {latest_ai_plan.is_active}")
                
                # 解析plan_data
                if latest_ai_plan.plan_data:
                    try:
                        ai_plan_json = latest_ai_plan.plan_data if isinstance(latest_ai_plan.plan_data, dict) else json.loads(latest_ai_plan.plan_data)
                        print(f"\n   📊 AI计划数据结构:")
                        print(f"      顶层字段: {list(ai_plan_json.keys())}")
                        
                        if 'days' in ai_plan_json:
                            print(f"      总天数: {len(ai_plan_json['days'])}")
                            # 统计有任务的天数
                            days_with_tasks = sum(1 for day in ai_plan_json['days'] if day.get('parts'))
                            print(f"      有任务的天数: {days_with_tasks}")
                        
                        if 'taskSummary' in ai_plan_json:
                            print(f"      任务数量: {len(ai_plan_json['taskSummary'])}")
                            for i, task in enumerate(ai_plan_json['taskSummary'], 1):
                                print(f"         任务{i}: {task.get('name', 'N/A')}")
                        
                        if 'aiSummary' in ai_plan_json:
                            summary = ai_plan_json['aiSummary']
                            print(f"\n   🤖 AI摘要信息:")
                            print(f"      类型: {type(summary)}")
                            if isinstance(summary, dict):
                                print(f"      AI摘要字段: {list(summary.keys())[:5]}")
                        
                        # 显示数据示例
                        print(f"\n   📄 AI计划数据预览 (前40行):")
                        json_str = json.dumps(ai_plan_json, indent=2, ensure_ascii=False)
                        all_lines = json_str.split('\n')
                        for line in all_lines[:40]:
                            print(f"      {line}")
                        if len(all_lines) > 40:
                            print(f"      ... (还有 {len(all_lines) - 40} 行)")
                            
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"      ❌ JSON解析失败: {e}")
                else:
                    print(f"      ⚠️ plan_data 为空")
            else:
                print("   ⚠️ 没有找到ai_chat_userstudyplan记录")
                
        except User.DoesNotExist:
            print(f"   ❌ 没有找到对应的User对象 (username={account.student_id})")
            print(f"   提示: ai_chat_userstudyplan表需要User对象关联")
        
        # 4. 对比两个表的最新计划时间
        print(f"\n{'='*80}")
        print("⏰ 时间对比:")
        print("="*80)
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(username=account.student_id)
            ai_plans = UserStudyPlan.objects.filter(user=user).order_by('-created_at')
            
            if study_plans.exists() and ai_plans.exists():
                study_time = study_plans.first().created_at
                ai_time = ai_plans.first().created_at
                print(f"   study_plan 最新时间: {study_time}")
                print(f"   ai_chat_userstudyplan 最新时间: {ai_time}")
                
                time_diff = abs((study_time - ai_time).total_seconds())
                if time_diff < 5:
                    print(f"   ✅ 两个表的数据同步 (时间差: {time_diff:.2f}秒)")
                else:
                    print(f"   ⚠️ 可能不同步 (时间差: {time_diff:.2f}秒)")
            elif not study_plans.exists():
                print("   ⚠️ study_plan 表中没有数据")
            elif not ai_plans.exists():
                print("   ⚠️ ai_chat_userstudyplan 表中没有数据")
        except User.DoesNotExist:
            print(f"   ⚠️ 无法对比 - User对象不存在")
        
        # 5. 检查数据库连接信息
        print(f"\n{'='*80}")
        print("🗄️ 数据库信息:")
        print("="*80)
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE(), VERSION()")
            db_info = cursor.fetchone()
            print(f"   当前数据库: {db_info[0]}")
            print(f"   数据库版本: {db_info[1]}")
            
            cursor.execute("SHOW VARIABLES LIKE 'hostname'")
            result = cursor.fetchone()
            if result:
                print(f"   主机名: {result[1]}")
        
        print(f"\n{'='*80}")
        print("✅ 检查完成!")
        print("="*80)
        
    except StudentAccount.DoesNotExist:
        print("❌ 没有找到z1234567用户")
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_z1234567_plans()
