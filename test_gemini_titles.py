#!/usr/bin/env python3
"""
测试Gemini生成的标题是否正确传递到前端
"""
import os
import sys
import django
from pathlib import Path

# 添加Django项目路径
project_root = Path(__file__).parent / 'django_backend'
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
django.setup()

from ai_module.plan_generator import generate_plan
from datetime import datetime, timedelta
import json

def test_gemini_titles():
    """测试Gemini生成的标题"""
    print("🧪 测试Gemini标题生成...")
    
    # 测试数据
    test_preferences = {
        'dailyHours': 4,
        'weeklyStudyDays': 5,
        'avoidDays': ['Sat', 'Sun']
    }
    
    test_tasks = [
        {
            'id': 'COMP9900_1',
            'task': 'COMP9900 - Frontend Assignment',
            'dueDate': (datetime.now() + timedelta(days=14)).isoformat(),
            'detailPdfPath': None
        },
        {
            'id': 'COMP9900_2', 
            'task': 'COMP9900 - Backend Project',
            'dueDate': (datetime.now() + timedelta(days=21)).isoformat(),
            'detailPdfPath': None
        }
    ]
    
    print(f"📋 测试任务: {len(test_tasks)} 个")
    for task in test_tasks:
        print(f"  - {task['task']}")
    
    # 生成AI计划
    result = generate_plan(test_preferences, test_tasks)
    
    if not result or not result.get('ok'):
        print("❌ AI计划生成失败")
        return False
    
    print("✅ AI计划生成成功!")
    print(f"📅 计划周数: {len(result.get('days', []))}")
    
    # 检查aiSummary中的标题
    ai_summary = result.get('aiSummary', {})
    tasks = ai_summary.get('tasks', [])
    
    print(f"\n🔍 AI摘要任务数: {len(tasks)}")
    for i, task in enumerate(tasks):
        print(f"\n任务 {i+1}: {task.get('taskTitle')}")
        parts = task.get('parts', [])
        print(f"  Parts数量: {len(parts)}")
        for j, part in enumerate(parts):
            title = part.get('title', 'No title')
            print(f"    Part {j+1}: {title}")
            if 'Part' in title and ('-' in title):
                print(f"      ✅ 包含Gemini生成的特定标题格式")
            else:
                print(f"      ⚠️  标题格式可能不是Gemini生成的")
    
    # 检查days中的blocks标题
    print(f"\n📅 检查每日计划中的标题:")
    days = result.get('days', [])
    for day in days[:3]:  # 只检查前3天
        date = day.get('date')
        blocks = day.get('blocks', [])
        print(f"\n日期 {date}: {len(blocks)} 个blocks")
        for block in blocks:
            title = block.get('title', 'No title')
            task_id = block.get('taskId', 'No taskId')
            print(f"  - {task_id}: {title}")
            if 'Part' in title and ('-' in title):
                print(f"    ✅ Gemini标题格式正确")
            else:
                print(f"    ⚠️  可能不是Gemini标题")
    
    return True

if __name__ == '__main__':
    test_gemini_titles()