#!/usr/bin/env python3
import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# 配置Django
django.setup()

def test_correct_login():
    """测试正确的登录信息"""
    try:
        print("=== 测试1234567账号登录 ===")
        from django.test import Client
        
        client = Client()
        
        # 测试正确的账号密码
        login_data = {
            'student_id': '1234567',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', login_data, content_type='application/json')
        print(f"1234567登录POST请求状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功!")
            print(f"返回的token: {result.get('data', {}).get('token', 'N/A')[:20]}...")
            print(f"用户信息: {result.get('data', {}).get('user', {})}")
        else:
            print(f"❌ 登录失败")
            print(f"错误响应: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ 测试登录时出错: {e}")

if __name__ == "__main__":
    test_correct_login()