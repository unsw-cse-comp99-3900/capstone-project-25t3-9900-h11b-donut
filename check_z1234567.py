#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def check_z1234567():
    """检查z1234567账号"""
    try:
        from stu_accounts.models import StudentAccount
        from django.db import connection
        
        print("=== 检查z1234567账号 ===")
        
        # 检查所有包含1234567的账号
        with connection.cursor() as cursor:
            cursor.execute("SELECT student_id, name, email FROM accounts_studentaccount WHERE student_id LIKE '%1234567%';")
            accounts = cursor.fetchall()
            
            if accounts:
                print(f"找到 {len(accounts)} 个包含1234567的账号:")
                for acc in accounts:
                    print(f"  ID: {acc[0]}, 姓名: {acc[1]}, 邮箱: {acc[2]}")
            else:
                print("❌ 没有找到任何包含1234567的账号")
                
            # 检查所有学生账号ID
            cursor.execute("SELECT student_id FROM accounts_studentaccount ORDER BY student_id;")
            all_accounts = cursor.fetchall()
            print(f"\n数据库中所有学生ID:")
            for acc in all_accounts[:10]:  # 只显示前10个
                print(f"  {acc[0]}")
            if len(all_accounts) > 10:
                print(f"  ... 还有 {len(all_accounts) - 10} 个账号")
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_z1234567()
