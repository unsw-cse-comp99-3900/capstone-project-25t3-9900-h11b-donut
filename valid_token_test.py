#!/usr/bin/env python3
"""
使用有效token测试 AI 计划生成
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.test import RequestFactory
from plans.views import generate_ai_plan
from stu_accounts.models import StudentAccount
from utils.auth import make_token
import json

def test_with_valid_token():
    """使用有效token测试"""
    print("🧪 开始测试 generate_ai_plan（有效token）...")
    
    # 获取测试学生
    try:
        student = StudentAccount.objects.get(student_id="z1234567")
        print(f"✅ 找到学生: {student.name} (ID: {student.student_id})")
    except StudentAccount.DoesNotExist:
        print("❌ 学生 z1234567 不存在")
        return
    
    # 创建有效的token并更新学生记录
    valid_token = make_token()
    student.current_token = valid_token
    student.save()
    print(f"🔑 生成有效token: {valid_token[:20]}...")
    
    # 创建伪造的请求
    factory = RequestFactory()
    
    # 模拟POST请求
    request = factory.post('/api/generate', 
                         data=json.dumps({"timezone": "Australia/Sydney"}), 
                         content_type='application/json')
    
    # 设置有效的认证头
    request.META['HTTP_AUTHORIZATION'] = f'Bearer {valid_token}'
    
    print("📤 发送AI计划生成请求...")
    
    try:
        response = generate_ai_plan(request)
        print(f"📥 响应状态码: {response.status_code}")
        
        # 解析响应
        response_content = response.content.decode()
        print(f"📥 响应内容: {response_content}")
        
        # 尝试解析JSON
        try:
            response_data = json.loads(response_content)
            print(f"📊 响应分析:")
            print(f"  - success: {response_data.get('success')}")
            print(f"  - message: {response_data.get('message')}")
            
            if response_data.get('success'):
                data = response_data.get('data')
                if isinstance(data, dict):
                    print(f"  - data keys: {list(data.keys())}")
                    if 'ok' in data:
                        print(f"  - AI result ok: {data.get('ok')}")
                    if 'message' in data:
                        print(f"  - AI result message: {data.get('message')}")
                    if 'days' in data:
                        print(f"  - days count: {len(data.get('days', []))}")
                    if 'aiSummary' in data:
                        ai_summary = data.get('aiSummary', {})
                        if 'tasks' in ai_summary:
                            print(f"  - AI任务数: {len(ai_summary.get('tasks', []))}")
                else:
                    print(f"  - data type: {type(data)}")
                
                print("✅ AI计划生成测试成功!")
            else:
                print(f"❌ AI计划生成失败: {response_data.get('message')}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_valid_token()