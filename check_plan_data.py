#!/usr/bin/env python3
import os
import sys
import django
import json

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def check_study_plans():
    """检查学习计划数据"""
    try:
        from plans.models import StudyPlan
        from django.db import connection
        
        print("=== 检查Study Plan数据 ===")
        
        # 检查study_plan表中的数据
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM study_plan;")
            count = cursor.fetchone()[0]
            print(f"学习计划总数: {count}")
            
            if count > 0:
                # 获取最近的几个计划
                cursor.execute("""
                    SELECT id, student_id, course_id, created_at 
                    FROM study_plan 
                    ORDER BY created_at DESC 
                    LIMIT 5;
                """)
                plans = cursor.fetchall()
                
                print(f"\n最近的{len(plans)}个学习计划:")
                for plan in plans:
                    print(f"\n计划ID: {plan[0]}")
                    print(f"  学生ID: {plan[1]}")
                    print(f"  课程ID: {plan[2]}")
                    print(f"  创建时间: {plan[3]}")
                    
                    # 获取计划详情
                    plan_obj = StudyPlan.objects.get(id=plan[0])
                    print(f"  计划内容存在: {bool(plan_obj.plan_content)}")
                    
                    if plan_obj.plan_content:
                        try:
                            plan_data = json.loads(plan_obj.plan_content)
                            print(f"  JSON结构: ✅ 有效")
                            print(f"  数据键: {list(plan_data.keys())}")
                            
                            # 检查是否有parts字段
                            if 'parts' in plan_data:
                                parts = plan_data['parts']
                                print(f"  计划部分数量: {len(parts)}")
                                
                                # 显示第一个part的结构
                                if parts:
                                    first_part = parts[0]
                                    print(f"\n  第一个Part结构:")
                                    print(f"    键: {list(first_part.keys())}")
                                    if 'title' in first_part:
                                        print(f"    标题: {first_part['title']}")
                                    if 'tasks' in first_part:
                                        print(f"    任务数量: {len(first_part['tasks'])}")
                                        if first_part['tasks']:
                                            print(f"    第一个任务: {list(first_part['tasks'][0].keys())}")
                            
                            # 显示完整JSON（缩略）
                            json_str = json.dumps(plan_data, indent=2, ensure_ascii=False)
                            if len(json_str) > 500:
                                print(f"\n  JSON内容（前500字符）:\n{json_str[:500]}...")
                            else:
                                print(f"\n  JSON内容:\n{json_str}")
                                
                        except json.JSONDecodeError as e:
                            print(f"  JSON解析错误: {e}")
                    else:
                        print(f"  ⚠️ 计划内容为空")
                        
        # 检查AI生成的计划
        print("\n\n=== 检查AI Chat中的Study Plan数据 ===")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ai_chat_userstudyplan;")
            ai_count = cursor.fetchone()[0]
            print(f"AI Chat学习计划总数: {ai_count}")
            
            if ai_count > 0:
                cursor.execute("""
                    SELECT student_id, course_id, plan_content, created_at
                    FROM ai_chat_userstudyplan
                    ORDER BY created_at DESC
                    LIMIT 3;
                """)
                ai_plans = cursor.fetchall()
                
                print(f"\n最近的{len(ai_plans)}个AI生成计划:")
                for idx, ai_plan in enumerate(ai_plans, 1):
                    print(f"\n计划 #{idx}:")
                    print(f"  学生ID: {ai_plan[0]}")
                    print(f"  课程ID: {ai_plan[1]}")
                    print(f"  创建时间: {ai_plan[3]}")
                    
                    plan_content = ai_plan[2]
                    if plan_content:
                        try:
                            plan_data = json.loads(plan_content)
                            print(f"  JSON结构: ✅ 有效")
                            print(f"  数据键: {list(plan_data.keys())}")
                            
                            if 'parts' in plan_data:
                                print(f"  Parts数量: {len(plan_data['parts'])}")
                                
                        except json.JSONDecodeError as e:
                            print(f"  JSON解析错误: {e}")
                    else:
                        print(f"  ⚠️ 计划内容为空")
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_study_plans()
