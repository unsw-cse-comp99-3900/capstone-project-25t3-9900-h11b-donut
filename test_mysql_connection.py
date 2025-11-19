#!/usr/bin/env python3
import os
import sys
import django

# 添加项目路径
sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# 配置Django
django.setup()

def test_mysql_connection():
    """测试MySQL连接"""
    try:
        from django.db import connection
        
        print("=== 测试TiDB Cloud MySQL连接 ===")
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"✅ 数据库连接成功!")
            print(f"数据库版本: {version[0]}")
            
            # 检查是否有学生账号表
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\n数据库中的表数量: {len(tables)}")
            
            # 检查学生账号
            cursor.execute("SELECT COUNT(*) FROM accounts_studentaccount;")
            count = cursor.fetchone()[0]
            print(f"学生账号数量: {count}")
            
            if count > 0:
                cursor.execute("SELECT student_id, name, email FROM accounts_studentaccount LIMIT 5;")
                accounts = cursor.fetchall()
                print("\n前5个学生账号:")
                for acc in accounts:
                    print(f"  ID: {acc[0]}, 姓名: {acc[1]}, 邮箱: {acc[2]}")
                    
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n如果连接失败，可能需要：")
        print("1. 检查网络连接")
        print("2. 确认TiDB Cloud服务正常")
        print("3. 检查数据库凭证是否正确")

if __name__ == "__main__":
    test_mysql_connection()
