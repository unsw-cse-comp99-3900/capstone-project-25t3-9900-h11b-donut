#!/usr/bin/env python3
"""快速查询TiDB中的学生计划表"""
import os
import sys
import django

sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.db import connection

def execute_query(sql, description=""):
    """执行SQL查询并打印结果"""
    if description:
        print(f"\n{'='*80}")
        print(f"📊 {description}")
        print('='*80)
    
    with connection.cursor() as cursor:
        cursor.execute(sql)
        
        # 获取列名
        columns = [col[0] for col in cursor.description]
        print(f"\n列: {', '.join(columns)}\n")
        
        # 获取结果
        rows = cursor.fetchall()
        
        if not rows:
            print("(空结果)")
            return
        
        # 打印结果
        for i, row in enumerate(rows, 1):
            print(f"行 {i}:")
            for col, val in zip(columns, row):
                # 如果是长文本,只显示前100个字符
                if isinstance(val, str) and len(val) > 100:
                    val = val[:100] + "..."
                print(f"  {col}: {val}")
            print()
        
        print(f"总计: {len(rows)} 条记录")

def main():
    print("="*80)
    print("🗄️ TiDB学生计划表查询工具")
    print("="*80)
    
    # 1. 查询ai_chat_userstudyplan表
    execute_query("""
        SELECT id, user_id, created_at, is_active,
               CASE 
                   WHEN LENGTH(plan_data) > 100 THEN CONCAT(SUBSTRING(plan_data, 1, 100), '...')
                   ELSE plan_data 
               END as plan_data_preview
        FROM ai_chat_userstudyplan 
        ORDER BY created_at DESC 
        LIMIT 5
    """, "ai_chat_userstudyplan 表 (最新5条)")
    
    # 2. 查询z1234567用户的AI计划
    execute_query("""
        SELECT acup.id, acup.created_at, acup.is_active,
               au.username as student_id
        FROM ai_chat_userstudyplan acup
        JOIN auth_user au ON acup.user_id = au.id
        WHERE au.username = 'z1234567'
        ORDER BY acup.created_at DESC
    """, "z1234567用户的AI计划")
    
    # 3. 查询study_plan表
    execute_query("""
        SELECT id, student_id, week_start_date, source, 
               week_offset, created_at
        FROM study_plan 
        ORDER BY created_at DESC 
        LIMIT 5
    """, "study_plan 表 (最新5条)")
    
    # 4. 查询z1234567的study_plan
    execute_query("""
        SELECT id, student_id, week_start_date, source, created_at
        FROM study_plan 
        WHERE student_id = 'z1234567'
        ORDER BY created_at DESC
    """, "z1234567用户的学习计划")
    
    # 5. 查询z1234567最新计划的任务项
    execute_query("""
        SELECT spi.id, spi.course_code, spi.part_title, 
               spi.scheduled_date, spi.minutes, spi.completed
        FROM study_plan_item spi
        JOIN study_plan sp ON spi.plan_id = sp.id
        WHERE sp.student_id = 'z1234567'
        ORDER BY sp.created_at DESC, spi.scheduled_date ASC
        LIMIT 10
    """, "z1234567最新计划的任务项 (前10条)")
    
    # 6. 统计信息
    print(f"\n{'='*80}")
    print("📈 统计信息")
    print('='*80)
    
    with connection.cursor() as cursor:
        # AI计划总数
        cursor.execute("SELECT COUNT(*) FROM ai_chat_userstudyplan")
        ai_plan_count = cursor.fetchone()[0]
        print(f"\nAI计划总数: {ai_plan_count}")
        
        # 学习计划总数
        cursor.execute("SELECT COUNT(*) FROM study_plan")
        study_plan_count = cursor.fetchone()[0]
        print(f"学习计划总数: {study_plan_count}")
        
        # 计划项总数
        cursor.execute("SELECT COUNT(*) FROM study_plan_item")
        item_count = cursor.fetchone()[0]
        print(f"计划项总数: {item_count}")
        
        # z1234567的计划数
        cursor.execute("SELECT COUNT(*) FROM study_plan WHERE student_id = 'z1234567'")
        z_plan_count = cursor.fetchone()[0]
        print(f"\nz1234567的计划数: {z_plan_count}")
    
    print(f"\n{'='*80}")
    print("✅ 查询完成!")
    print('='*80)

if __name__ == '__main__':
    main()
