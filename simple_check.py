#!/usr/bin/env python3
import os
import sys
import django
import json

sys.path.append('/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def simple_check():
    """简单检查"""
    try:
        from django.db import connection
        
        # 检查ai_chat_userstudyplan表结构
        print("=== ai_chat_userstudyplan 表字段 ===")
        with connection.cursor() as cursor:
            cursor.execute("DESCRIBE ai_chat_userstudyplan;")
            columns = cursor.fetchall()
            col_names = []
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
                col_names.append(col[0])
        
        # 获取最新一条数据
        print("\n=== 最新AI生成计划 ===")
        with connection.cursor() as cursor:
            # 使用实际的字段名
            cursor.execute(f"SELECT {', '.join(col_names)} FROM ai_chat_userstudyplan ORDER BY created_at DESC LIMIT 1;")
            row = cursor.fetchone()
            
            if row:
                for col_name, value in zip(col_names, row):
                    if col_name == 'plan_data':
                        if value:
                            print(f"\n{col_name}:")
                            try:
                                plan_json = json.loads(value)
                                print(f"  ✅ JSON有效")
                                print(f"  顶层字段: {list(plan_json.keys())}")
                                
                                if 'parts' in plan_json:
                                    print(f"  Parts数量: {len(plan_json['parts'])}")
                                    if plan_json['parts']:
                                        print(f"  第一个Part字段: {list(plan_json['parts'][0].keys())}")
                                
                                # 显示JSON片段
                                json_str = json.dumps(plan_json, indent=2, ensure_ascii=False)
                                print(f"\n  JSON内容（前800字符）:")
                                print(json_str[:800])
                                
                            except json.JSONDecodeError as e:
                                print(f"  ❌ JSON解析失败: {e}")
                        else:
                            print(f"{col_name}: None")
                    else:
                        print(f"{col_name}: {value}")
                        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_check()
