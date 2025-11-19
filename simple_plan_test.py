#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_simple():
    from courses.models import StudentEnrollment, CourseTask
    from stu_accounts.models import StudentAccount
    from ai_module.plan_generator import generate_plan
    
    print("=== 简单测试AI生成计划 ===\n")
    
    # 1. 找一个有课程的学生
    student = StudentAccount.objects.filter(student_id='z1234567').first()
    if not student:
        print("❌ 未找到学生")
        return
    
    print(f"学生: {student.student_id}")
    
    # 2. 获取任务
    enrollments = StudentEnrollment.objects.filter(student_id=student.student_id)
    course_codes = enrollments.values_list('course_code', flat=True)
    tasks = CourseTask.objects.filter(course_code__in=course_codes)
    
    print(f"课程数: {enrollments.count()}")
    print(f"任务数: {tasks.count()}\n")
    
    if not tasks:
        print("❌ 没有任务，无法生成计划")
        return
    
    # 3. 准备任务元数据
    tasks_meta = []
    for t in tasks:
        task_meta = {
            "id": f"{t.course_code}_{t.id}",
            "task": f"{t.course_code} - {t.title}",
            "dueDate": t.deadline.isoformat() if t.deadline else None,
            "detailPdfPath": t.url,
        }
        tasks_meta.append(task_meta)
        print(f"任务: {task_meta['task']}, 截止: {task_meta['dueDate']}")
    
    # 4. 准备偏好
    preferences = {
        "daily_hour_cap": 4,
        "weekly_study_days": 5,
        "avoid_days": ["Sun", "Sat"]
    }
    
    print(f"\n偏好: {preferences}\n")
    
    # 5. 调用AI生成
    print("🤖 调用AI生成计划...")
    try:
        result = generate_plan(preferences, tasks_meta, user_timezone='Australia/Sydney')
        
        print(f"\n✅ AI生成完成!")
        print(f"结果类型: {type(result)}")
        print(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        if result.get('ok'):
            print(f"  ok: {result['ok']}")
            print(f"  aiSummary: {'存在' if 'aiSummary' in result else '不存在'}")
            print(f"  days: {len(result.get('days', []))} 天")
            print(f"  taskSummary: {'存在' if 'taskSummary' in result else '不存在'}")
            
            # 检查days内容
            if result.get('days'):
                total_blocks = sum(len(day.get('blocks', [])) for day in result['days'])
                print(f"  总任务块数: {total_blocks}")
        else:
            print(f"  ❌ ok=False")
            print(f"  message: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ AI生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
