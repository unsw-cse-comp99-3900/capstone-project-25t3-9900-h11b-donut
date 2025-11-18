#!/usr/bin/env python3
"""
检查z1234567用户的token状态
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from stu_accounts.models import StudentAccount
import datetime

def check_token_status():
    """检查token状态"""
    print("🔍 检查学生token状态...")
    
    try:
        student = StudentAccount.objects.get(student_id="z1234567")
        print(f"✅ 找到学生: {student.name} (ID: {student.student_id})")
        print(f"🔑 当前token: {student.current_token}")
        print(f"🕐 Token签发时间: {student.token_issued_at}")
        
        # 检查token是否过期（假设token有效期为24小时）
        if student.token_issued_at:
            now = datetime.datetime.now(datetime.timezone.utc)
            age = now - student.token_issued_at
            print(f"⏰ Token年龄: {age}")
            
            if age.total_seconds() > 24 * 60 * 60:  # 超过24小时
                print("⚠️ Token可能已过期")
            else:
                print("✅ Token看起来仍然有效")
        else:
            print("⚠️ 没有token签发时间记录")
            
        # 如果没有token或token过期，生成新的
        if not student.current_token:
            from utils.auth import make_token
            new_token = make_token()
            student.current_token = new_token
            student.token_issued_at = datetime.datetime.now(datetime.timezone.utc)
            student.save()
            print(f"🔧 生成了新token: {new_token[:20]}...")
            print("💡 请在前端localStorage中设置 'auth_token' 为这个新token")
        
    except StudentAccount.DoesNotExist:
        print("❌ 学生 z1234567 不存在")

if __name__ == "__main__":
    check_token_status()