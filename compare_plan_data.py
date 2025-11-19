#!/usr/bin/env python3
"""对比前端显示的计划和数据库中的计划数据"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth.models import User
from stu_accounts.models import StudentAccount
from ai_chat.models import UserStudyPlan
import json

def compare_plans():
    print("="*80)
    print("🔍 对比z1234567用户的前端显示计划与数据库计划")
    print("="*80)
    
    # 前端显示的任务信息
    frontend_tasks = [
        {"course": "COMP9331", "task": "9331task1", "parts": [
            "Part 1 - Setup & Research",
            "Part 2 - Part A: Schema Design",
            "Part 3 - Part B: SQL Queries",
            "Part 4 - Part C: Indexing & Performance",
            "Part 5 - Documentation & Review"
        ]},
        {"course": "COMP9417", "task": "Assignmtn1", "parts": [
            "Part 1 - Project Setup & Data Mocking",
            "Part 2 - User Authentication",
            "Part 3 - Dashboard Core & Metrics Display",
            "Part 4 - Data Visualization Implementation",
            "Part 5 - Responsiveness, UI/UX & Performance",
            "Part 6 - Code Refinement & Deliverables"
        ]},
        {"course": "COMP9900", "task": "task1", "parts": [
            "Part 1 - Setup & Initial Research",
            "Part 2 - Basic Authentication UI",
            "Part 3 - Dashboard Layout Shell & Metrics Placeholders"
        ]}
    ]
    
    print("\n📱 前端显示的计划:")
    print("="*80)
    total_parts = 0
    for task in frontend_tasks:
        print(f"\n🎯 {task['course']} - {task['task']}:")
        for i, part in enumerate(task['parts'], 1):
            print(f"   Part {i}: {part}")
            total_parts += 1
    
    print(f"\n   ✅ 总计: {len(frontend_tasks)} 个任务, {total_parts} 个Parts")
    
    # 从数据库读取AI计划
    print("\n" + "="*80)
    print("🗄️ 数据库中的AI计划:")
    print("="*80)
    
    try:
        account = StudentAccount.objects.get(student_id='z1234567')
        user = User.objects.get(username=account.student_id)
        
        ai_plans = UserStudyPlan.objects.filter(user=user, is_active=True).order_by('-created_at')
        
        if not ai_plans.exists():
            print("❌ 没有找到激活的AI计划")
            return
        
        latest_plan = ai_plans.first()
        plan_data = latest_plan.plan_data if isinstance(latest_plan.plan_data, dict) else json.loads(latest_plan.plan_data)
        
        print(f"\n📊 数据库计划信息:")
        print(f"   计划ID: {latest_plan.id}")
        print(f"   创建时间: {latest_plan.created_at}")
        print(f"   激活状态: {latest_plan.is_active}")
        
        # 分析taskSummary
        if 'taskSummary' in plan_data:
            task_summary = plan_data['taskSummary']
            print(f"\n   任务总数: {len(task_summary)}")
            
            db_total_parts = 0
            for i, task in enumerate(task_summary, 1):
                task_name = task.get('name', 'N/A')
                course_id = task.get('courseId', 'N/A')
                parts = task.get('parts', [])
                
                print(f"\n🎯 任务{i}: {course_id} - {task_name}")
                print(f"   Parts数量: {len(parts)}")
                
                for j, part in enumerate(parts, 1):
                    part_title = part.get('title', 'N/A')
                    part_minutes = part.get('minutes', 0)
                    print(f"      Part {j}: {part_title} ({part_minutes}分钟)")
                    db_total_parts += 1
            
            print(f"\n   ✅ 总计: {len(task_summary)} 个任务, {db_total_parts} 个Parts")
        
        # 对比分析
        print("\n" + "="*80)
        print("📊 对比分析:")
        print("="*80)
        
        # 对比任务数量
        frontend_task_count = len(frontend_tasks)
        db_task_count = len(plan_data.get('taskSummary', []))
        
        print(f"\n任务数量:")
        print(f"   前端显示: {frontend_task_count} 个任务")
        print(f"   数据库: {db_task_count} 个任务")
        if frontend_task_count == db_task_count:
            print(f"   ✅ 任务数量一致")
        else:
            print(f"   ❌ 任务数量不一致!")
        
        # 对比Parts数量
        print(f"\nParts数量:")
        print(f"   前端显示: {total_parts} 个Parts")
        print(f"   数据库: {db_total_parts} 个Parts")
        if total_parts == db_total_parts:
            print(f"   ✅ Parts数量一致")
        else:
            print(f"   ❌ Parts数量不一致!")
        
        # 详细对比每个任务
        print(f"\n详细对比:")
        task_summary = plan_data.get('taskSummary', [])
        
        for i, (fe_task, db_task) in enumerate(zip(frontend_tasks, task_summary), 1):
            fe_course = fe_task['course']
            db_course = db_task.get('courseId', '')
            
            print(f"\n任务{i}:")
            print(f"   前端课程: {fe_course}")
            print(f"   数据库课程: {db_course}")
            
            if fe_course == db_course:
                print(f"   ✅ 课程匹配")
            else:
                print(f"   ❌ 课程不匹配!")
            
            fe_parts = fe_task['parts']
            db_parts = [p.get('title', '') for p in db_task.get('parts', [])]
            
            print(f"   前端Parts数: {len(fe_parts)}")
            print(f"   数据库Parts数: {len(db_parts)}")
            
            # 对比每个Part标题
            all_match = True
            for j, (fe_part, db_part) in enumerate(zip(fe_parts, db_parts), 1):
                if fe_part == db_part:
                    print(f"      ✅ Part {j}: {fe_part}")
                else:
                    print(f"      ❌ Part {j} 不匹配:")
                    print(f"         前端: {fe_part}")
                    print(f"         数据库: {db_part}")
                    all_match = False
            
            if all_match and len(fe_parts) == len(db_parts):
                print(f"   ✅ 所有Parts标题完全匹配!")
        
        # 检查days数据
        print("\n" + "="*80)
        print("📅 Days数据分析:")
        print("="*80)
        
        if 'days' in plan_data:
            days = plan_data['days']
            print(f"   总天数: {len(days)}")
            
            days_with_parts = []
            for day_idx, day in enumerate(days):
                if day.get('parts') and len(day.get('parts', [])) > 0:
                    days_with_parts.append(day_idx)
            
            print(f"   有任务的天数: {len(days_with_parts)}")
            print(f"   有任务的天索引: {days_with_parts}")
            
            # 前端显示的映射
            print(f"\n   前端显示的周计划映射:")
            print(f"   第0天(周一): 8个任务项")
            print(f"   第1天(周二): 6个任务项")
            print(f"   第2天(周三): 0个任务项")
            
            # 对比数据库的days
            print(f"\n   数据库days分布:")
            for i in range(min(7, len(days))):
                day = days[i]
                parts_count = len(day.get('parts', []))
                print(f"   第{i}天: {parts_count} 个任务项")
                if parts_count > 0 and i < 3:
                    # 显示前3天的任务详情
                    for part in day.get('parts', []):
                        print(f"      - {part.get('courseId', 'N/A')}: {part.get('title', 'N/A')}")
        
        print("\n" + "="*80)
        print("✅ 对比完成!")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    compare_plans()
