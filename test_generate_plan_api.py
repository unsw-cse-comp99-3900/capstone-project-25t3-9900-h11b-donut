#!/usr/bin/env python3
import os
import sys
import django
import json

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_generate_plan():
    """测试生成计划API"""
    try:
        from django.test import Client
        from stu_accounts.models import StudentAccount
        
        print("=" * 100)
        print(" " * 35 + "测试AI生成计划API")
        print("=" * 100)
        
        # 1. 登录获取token
        print("\n【1】登录获取token")
        print("-" * 100)
        client = Client()
        
        # 先找一个有课程的学生
        from courses.models import StudentEnrollment
        enrollments = StudentEnrollment.objects.all()[:1]
        
        if not enrollments:
            print("❌ 没有学生选课记录")
            return
            
        student_id = enrollments[0].student_id
        print(f"使用学生ID: {student_id}")
        
        # 查找这个学生账号
        try:
            student = StudentAccount.objects.get(student_id=student_id)
            print(f"学生信息: {student.name}, {student.email}")
        except StudentAccount.DoesNotExist:
            print(f"❌ 未找到学生账号: {student_id}")
            return
        
        # 检查该学生的课程
        student_courses = StudentEnrollment.objects.filter(student_id=student_id)
        print(f"\n学生选课数量: {student_courses.count()}")
        for enrollment in student_courses[:3]:
            print(f"  - {enrollment.course_code}")
        
        # 检查该学生的任务
        from courses.models import CourseTask
        course_codes = student_courses.values_list('course_code', flat=True)
        tasks = CourseTask.objects.filter(course_code__in=course_codes)
        print(f"\n任务数量: {tasks.count()}")
        for task in tasks[:3]:
            print(f"  - {task.course_code}: {task.title}, 截止: {task.deadline}")
        
        # 2. 直接调用generate_ai_plan函数
        print("\n【2】直接调用generate_ai_plan函数")
        print("-" * 100)
        
        from plans.views import generate_ai_plan
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/api/plans/generate')
        
        # 模拟认证
        request.account = student
        request.session = {}
        
        response = generate_ai_plan(request)
        response_data = json.loads(response.content.decode())
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应success: {response_data.get('success')}")
        print(f"响应message: {response_data.get('message', 'N/A')}")
        
        if response_data.get('data'):
            data = response_data['data']
            print(f"\n✅ 返回了数据!")
            print(f"数据类型: {type(data)}")
            print(f"数据键: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            if 'aiSummary' in data:
                print(f"  aiSummary: ✅ 存在")
                if 'tasks' in data['aiSummary']:
                    print(f"    tasks数量: {len(data['aiSummary']['tasks'])}")
            else:
                print(f"  aiSummary: ❌ 不存在")
            
            if 'days' in data:
                print(f"  days: ✅ 存在 ({len(data['days'])}天)")
            else:
                print(f"  days: ❌ 不存在")
        else:
            print(f"\n❌ 返回的data为空!")
            if response_data.get('message'):
                print(f"错误信息: {response_data['message']}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_plan()
