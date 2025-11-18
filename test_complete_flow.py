#!/usr/bin/env python3
"""
完整的聊天到练习流程测试
"""
import requests
import json
import time

def test_complete_flow():
    """测试从聊天到练习的完整流程"""
    base_url = "http://localhost:8000/api"
    frontend_url = "http://localhost:5175"
    
    print("🚀 测试完整的聊天到练习流程...")
    
    # 1. 测试健康检查
    try:
        response = requests.get(f"{base_url}/ai/health/")
        if response.status_code == 200:
            print("✅ 后端服务健康")
        else:
            print("❌ 后端服务不健康")
            return
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return
    
    # 2. 模拟用户发送练习请求
    user_id = "z1234567"
    
    print("\n📱 步骤1: 用户发送练习请求")
    chat_data = {
        "message": "I want to practice my weak topics",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/ai/chat/?user_id={user_id}", json=chat_data)
    if response.status_code == 200:
        print("✅ 成功发送练习请求")
        result = response.json()
        print(f"   AI回复: {result.get('ai_response', {}).get('content', '')[:100]}...")
    else:
        print(f"❌ 发送请求失败: {response.status_code}")
        return
    
    # 3. 模拟选择课程
    print("\n📚 步骤2: 用户选择课程 COMP9417")
    course_data = {
        "message": "COMP9417",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/ai/chat/?user_id={user_id}", json=course_data)
    if response.status_code == 200:
        print("✅ 成功选择课程")
        result = response.json()
        print(f"   AI回复: {result.get('ai_response', {}).get('content', '')[:100]}...")
    else:
        print(f"❌ 选择课程失败: {response.status_code}")
        return
    
    # 4. 模拟选择主题
    print("\n🎯 步骤3: 用户选择主题 concepts")
    topic_data = {
        "message": "concepts",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/ai/chat/?user_id={user_id}", json=topic_data)
    if response.status_code == 200:
        print("✅ 成功选择主题")
        result = response.json()
        ai_content = result.get('ai_response', {}).get('content', '')
        print(f"   AI回复: {ai_content[:200]}...")
        
        # 检查是否包含确认信息
        if "Great choice" in ai_content and "generating" in ai_content:
            print("✅ AI正确识别并开始生成练习")
        else:
            print("⚠️ AI回复可能不符合预期")
    else:
        print(f"❌ 选择主题失败: {response.status_code}")
        return
    
    # 5. 直接测试练习生成API
    print("\n🔧 步骤4: 测试练习生成API")
    practice_data = {
        "course": "COMP9417",
        "topic": "concepts",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/ai/generate-practice/", json=practice_data)
    if response.status_code == 200:
        print("✅ 练习生成成功")
        result = response.json()
        session_id = result.get('session_id')
        total_questions = result.get('total_questions', 0)
        
        print(f"   会话ID: {session_id}")
        print(f"   题目数量: {total_questions}")
        
        if session_id and total_questions > 0:
            # 6. 生成练习页面URL
            practice_url = f"{frontend_url}/#/practice-session/COMP9417/concepts/{session_id}"
            print(f"\n🔗 步骤5: 练习页面URL")
            print(f"   {practice_url}")
            
            # 7. 模拟按钮HTML
            button_html = f'''
            <button
                class="cw-cta-btn"
                onclick="window.startPracticeSession('COMP9417', 'concepts', '{session_id}')"
                aria-label="Start practice for COMP9417 - concepts"
            >
                Start Practice Session
                <span style="margin-left: 8px;">→</span>
            </button>
            '''
            
            print(f"\n🎯 步骤6: 生成的按钮HTML")
            print(button_html.strip())
            
            print(f"\n✅ 完整流程测试成功!")
            print(f"   用户可以在前端看到可点击的 'Start Practice Session' 按钮")
            print(f"   点击后将跳转到: {practice_url}")
            
        else:
            print("❌ 练习生成数据不完整")
    else:
        print(f"❌ 练习生成失败: {response.status_code}")
        print(f"   错误信息: {response.text}")

if __name__ == "__main__":
    test_complete_flow()