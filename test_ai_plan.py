#!/usr/bin/env python3
"""
测试 AI 计划生成功能
"""
import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000"

def test_ai_plan_generation():
    """测试AI计划生成"""
    # 模拟学生登录
    # 首先需要获取有效的token，这里使用一个测试学生账户
    login_data = {
        "student_id": "z1234567",  # 替换为实际的测试学生ID
        "password": "password123"   # 替换为实际的密码
    }
    
    try:
        # 1. 登录获取token
        print("🔐 尝试登录...")
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"登录响应状态: {login_response.status_code}")
        print(f"登录响应: {login_response.text}")
        
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return
            
        token = login_response.json().get("data", {}).get("token")
        if not token:
            print("❌ 未获取到token")
            return
            
        print(f"✅ 获取到token: {token[:20]}...")
        
        # 2. 调用AI计划生成API
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("\n🤖 调用AI计划生成API...")
        generate_response = requests.post(
            f"{BASE_URL}/api/generate", 
            headers=headers,
            json={"timezone": "Australia/Sydney"}
        )
        
        print(f"AI计划生成响应状态: {generate_response.status_code}")
        print(f"AI计划生成响应: {generate_response.text}")
        
        # 3. 分析响应
        if generate_response.status_code == 200:
            data = generate_response.json()
            if data.get("success"):
                print("✅ AI计划生成成功!")
                print(f"返回数据: {json.dumps(data.get('data', {}), indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ AI计划生成失败: {data.get('message')}")
        else:
            print(f"❌ API调用失败: HTTP {generate_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器，请确保Django服务器正在运行在 http://localhost:8000")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_ai_plan_generation()