#!/usr/bin/env python3
"""
调试完整的API流程
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from ai_chat.views import ChatView
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

def test_full_api_flow():
    print("=== 测试完整API流程 ===")
    
    # 创建视图实例
    chat_view = ChatView()
    
    # 模拟请求
    request = HttpRequest()
    request.method = 'POST'
    request._body = json.dumps({
        'message': 'goals',
        'user_id': '5215555'
    }).encode('utf-8')
    request.content_type = 'application/json'
    request.META = {
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': str(len(request._body))
    }
    request.user = AnonymousUser()
    
    print("发送请求...")
    try:
        response = chat_view.post(request)
        print(f"响应状态码: {response.status_code}")
        
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8')
            print(f"响应内容: {content}")
            
            try:
                data = json.loads(content)
                print(f"解析后的数据: {json.dumps(data, indent=2)}")
                
                if 'ai_response' in data:
                    ai_content = data['ai_response']['content']
                    print(f"AI回复内容: {ai_content}")
                    
                    if "I've generated" in ai_content:
                        print("✅ 生成成功!")
                    elif "Sorry, I encountered an issue" in ai_content:
                        print("❌ 生成失败!")
                    elif "I'm now generating" in ai_content:
                        print("⚠️ 只显示了生成中消息，没有实际生成")
                    else:
                        print("⚠️ 返回了意外结果")
                        
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
        else:
            print("响应没有content属性")
            
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_api_flow()