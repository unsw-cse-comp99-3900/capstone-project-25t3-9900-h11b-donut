#!/usr/bin/env python3
import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# 配置Django
django.setup()

def check_student_accounts():
    """检查学生账号"""
    try:
        from stu_accounts.models import StudentAccount
        
        print("=== 检查学生账号 ===")
        accounts = StudentAccount.objects.all()
        print(f"总共有 {len(accounts)} 个学生账号")
        
        for acc in accounts:
            print(f"ID: {acc.student_id}, 邮箱: {acc.email}, 姓名: {acc.name}")
            
        # 检查z1234567账号
        try:
            z_account = StudentAccount.objects.get(student_id="z1234567")
            print(f"\n找到z1234567账号:")
            print(f"  姓名: {z_account.name}")
            print(f"  学生ID: {z_account.student_id}")
            print(f"  邮箱: {z_account.email}")
            print(f"  密码哈希: {z_account.password_hash[:20]}...")
        except StudentAccount.DoesNotExist:
            print("\n❌ 没有找到z1234567账号")
            
    except Exception as e:
        print(f"❌ 检查学生账号时出错: {e}")

def check_login_view():
    """检查登录视图"""
    try:
        print("\n=== 检查登录视图 ===")
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # 测试登录页面访问
        response = client.get('/api/login/')
        print(f"登录页面GET请求状态: {response.status_code}")
        
        # 测试z1234567登录
        login_data = {
            'student_id': 'z1234567',
            'password': 'password123'
        }
        response = client.post('/api/login/', login_data, content_type='application/json')
        print(f"z1234567登录POST请求状态: {response.status_code}")
        if response.status_code != 200:
            print(f"错误响应: {response.content.decode()}")
        else:
            print("✅ z1234567登录成功")
            
    except Exception as e:
        print(f"❌ 检查登录视图时出错: {e}")

def check_database():
    """检查数据库连接"""
    try:
        print("\n=== 检查数据库连接 ===")
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"数据库中的表: {[table[0] for table in tables]}")
            
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()
    check_student_accounts()
    check_login_view()