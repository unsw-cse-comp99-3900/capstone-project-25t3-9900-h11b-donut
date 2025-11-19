#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def check_tables():
    """检查表结构"""
    try:
        from django.db import connection
        
        # 检查study_plan表结构
        print("=== study_plan 表结构 ===")
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE study_plan;")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
        
        # 检查ai_chat_userstudyplan表结构
        print("\n=== ai_chat_userstudyplan 表结构 ===")
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE ai_chat_userstudyplan;")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
                
        # 检查数据
        print("\n=== study_plan 表数据 ===")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM study_plan LIMIT 2;")
            rows = cursor.fetchall()
            cursor.execute("DESCRIBE study_plan;")
            columns = [col[0] for col in cursor.fetchall()]
            
            for idx, row in enumerate(rows, 1):
                print(f"\n记录 #{idx}:")
                for col_name, value in zip(columns, row):
                    if col_name == 'plan_content' and value:
                        print(f"  {col_name}: {str(value)[:100]}...")
                    else:
                        print(f"  {col_name}: {value}")
        
        # 检查AI生成的计划
        print("\n=== ai_chat_userstudyplan 表数据 ===")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM ai_chat_userstudyplan LIMIT 2;")
            rows = cursor.fetchall()
            cursor.execute("DESCRIBE ai_chat_userstudyplan;")
            columns = [col[0] for col in cursor.fetchall()]
            
            for idx, row in enumerate(rows, 1):
                print(f"\n记录 #{idx}:")
                for col_name, value in zip(columns, row):
                    if col_name == 'plan_content' and value:
                        print(f"  {col_name}: {str(value)[:200]}...")
                    else:
                        print(f"  {col_name}: {value}")
                
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
