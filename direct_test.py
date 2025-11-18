#!/usr/bin/env python3
"""
直接测试 AI 计划生成 API（通过Django的shell环境）
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from plans.views import generate_ai_plan
from stu_accounts.models import StudentAccount
import json

def test_generate_ai_plan():
    """直接测试generate_ai_plan视图"""
    print("🧪 开始测试 generate_ai_plan...")
    
    # 获取测试学生
    try:
        student = StudentAccount.objects.get(student_id="z1234567")
        print(f"✅ 找到学生: {student.name} (ID: {student.student_id})")
    except StudentAccount.DoesNotExist:
        print("❌ 学生 z1234567 不存在")
        return
    
    # 创建伪造的请求
    factory = RequestFactory()
    
    # 模拟POST请求（AI计划生成应该使用POST）
    request = factory.post('/api/generate', 
                         data=json.dumps({"timezone": "Australia/Sydney"}), 
                         content_type='application/json')
    
    # 手动设置认证信息
    request.session = {'student_id': student.student_id}
    request.META['HTTP_AUTHORIZATION'] = f'Bearer test_token_for_{student.student_id}'
    
    print("📤 发送AI计划生成请求...")
    
    try:
        response = generate_ai_plan(request)
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.content.decode()}")
        
        # 解析JSON响应
        if hasattr(response, 'content'):
            try:
                response_data = json.loads(response.content.decode())
                print(f"📊 响应数据结构:")
                print(f"  - success: {response_data.get('success')}")
                print(f"  - message: {response_data.get('message')}")
                if response_data.get('data'):
                    print(f"  - data keys: {list(response_data['data'].keys()) if isinstance(response_data['data'], dict) else type(response_data['data'])}")
                
                # 检查是否有错误信息
                if not response_data.get('success'):
                    print(f"❌ AI计划生成失败: {response_data.get('message')}")
                else:
                    print("✅ AI计划生成成功!")
                    
            except json.JSONDecodeError as e:
                print(f"❌ 无法解析JSON响应: {e}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_ai_plan()