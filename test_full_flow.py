#!/usr/bin/env python3
"""
测试完整数据流：模拟前端请求 → 后端API → AI模块
"""

import os
import sys
import django
import json
from pathlib import Path

# 添加Django项目路径
project_root = Path(__file__).parent / "django_backend"
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

# 导入Django模块
from django.test import RequestFactory
from plans.views import generate_ai_plan
from stu_accounts.models import StudentAccount
from courses.models import StudentEnrollment, CourseTask
from preferences.models import StudentPreference

def setup_test_data():
    """设置测试数据"""
    print("🔧 设置测试数据...")
    
    # 创建测试学生账户
    try:
        student = StudentAccount.objects.get(student_id="z5555555")
        created = False
    except StudentAccount.DoesNotExist:
        student = StudentAccount.objects.create(
            student_id="z5555555",
            email="test_flow@example.com",
            name="Test Student",
            password_hash="dummy_hash"
        )
        created = True
    
    if created:
        print(f"✅ 创建测试学生: {student.student_id}")
    else:
        print(f"✅ 使用现有学生: {student.student_id}")
    
    # 创建测试课程任务
    # 注释掉Final Assignment测试任务
    # task, created = CourseTask.objects.get_or_create(
    #     course_code="COMP9900",
    #     title="Final Assignment",
    #     defaults={
    #         "deadline": "2025-11-15",
    #         "brief": "Complete the final project",
    #         "url": "/task/comp9900/9900assignment2.pdf"
    #     }
    # )
    # 
    # if created:
    #     print(f"✅ 创建测试任务: {task.title}")
    # else:
    #     print(f"✅ 使用现有任务: {task.title}")
    
    # 创建学生选课记录
    enrollment, created = StudentEnrollment.objects.get_or_create(
        student_id=student.student_id,
        course_code="COMP9900"
    )
    
    if created:
        print(f"✅ 创建选课记录: {student.student_id} -> COMP9900")
    else:
        print(f"✅ 使用现有选课记录: {student.student_id} -> COMP9900")
    
    # 创建学生偏好
    pref, created = StudentPreference.objects.get_or_create(
        student=student,
        defaults={
            "daily_hours": 4,
            "weekly_study_days": 5,
            "avoid_days_bitmask": 96  # 避开周六周日 (64+32 = 96)
        }
    )
    
    if created:
        print(f"✅ 创建学生偏好")
    else:
        print(f"✅ 使用现有偏好")
    
    return student

def test_api_endpoint():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    
    # 设置测试数据
    student = setup_test_data()
    
    # 创建模拟请求
    factory = RequestFactory()
    request = factory.post('/api/generate', content_type='application/json')
    
    # 模拟认证 - 设置session和token
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.sessions.backends.db import SessionStore
    
    # 创建session
    session = SessionStore()
    session['student_id'] = student.student_id
    session.save()
    
    # 设置session到request
    request.session = session
    
    # 也可以通过token认证
    student.current_token = "test_token_12345"
    student.save()
    request.META['HTTP_AUTHORIZATION'] = f'Bearer {student.current_token}'
    
    try:
        # 调用API视图
        response = generate_ai_plan(request)
        
        print(f"✅ API响应状态: {response.status_code}")
        
        # 解析响应
        response_data = json.loads(response.content.decode('utf-8'))
        print(f"📊 响应数据结构: {list(response_data.keys())}")
        
        if response_data.get('success'):
            print("✅ API调用成功")
            ai_data = response_data.get('data', {})
            print(f"🤖 AI数据键: {list(ai_data.keys()) if isinstance(ai_data, dict) else 'Not a dict'}")
            
            if isinstance(ai_data, dict):
                if ai_data.get('ok'):
                    print("✅ AI计划生成成功")
                    if 'days' in ai_data:
                        print(f"📅 生成天数: {len(ai_data['days'])}")
                        # 显示前几天的数据
                        for i, day in enumerate(ai_data['days'][:3]):
                            blocks = day.get('blocks', [])
                            print(f"  Day {i+1} ({day.get('date')}): {len(blocks)} blocks")
                    
                    if 'aiSummary' in ai_data:
                        summary = ai_data['aiSummary']
                        if 'tasks' in summary:
                            print(f"📋 AI摘要任务数: {len(summary['tasks'])}")
                else:
                    print(f"⚠️ AI计划失败: {ai_data.get('message', '未知原因')}")
            
            return True
        else:
            print(f"❌ API调用失败: {response_data.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ API测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始测试完整数据流...\n")
    
    success = test_api_endpoint()
    
    print(f"\n📋 测试结果: {'✅ 成功' if success else '❌ 失败'}")
    
    if success:
        print("\n🎉 完整数据流测试通过！")
        print("💡 建议：在前端浏览器中测试实际的用户交互")
    else:
        print("\n⚠️ 数据流存在问题，请检查：")
        print("  1. 数据库中是否有有效的学生和课程数据")
        print("  2. AI模块配置是否正确")
        print("  3. PDF文件路径是否正确")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)