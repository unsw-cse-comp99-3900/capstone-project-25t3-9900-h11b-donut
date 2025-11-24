#!/usr/bin/env python3
"""检查RecentPracticeSession表和数据"""
import os
import django
import sys

# 配置Django环境
sys.path.insert(0, '/Users/duwenjia/capstone-project-25t3-9900-h11b-donut')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_backend.settings')
django.setup()

from ai_chat.models import RecentPracticeSession
from django.db import connection

# 检查表是否存在
with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES LIKE 'recent_practice_session'")
    result = cursor.fetchone()
    if result:
        print("✓ 表 recent_practice_session 存在")
    else:
        print("✗ 表 recent_practice_session 不存在")
        print("\n需要运行 migration:")
        print("cd django_backend && python manage.py migrate")
        sys.exit(1)

# 检查数据
print("\n=== 所有测试会话 ===")
sessions = RecentPracticeSession.objects.all().order_by('-completed_at')
print(f"共 {sessions.count()} 条记录\n")

for session in sessions[:5]:  # 显示最近5条
    print(f"Student: {session.student_id}")
    print(f"Session: {session.session_id}")
    print(f"Course: {session.course_code} - {session.topic}")
    print(f"Score: {session.total_score}/{session.max_score} ({session.percentage:.1f}%)")
    print(f"Questions: {session.questions_count}")
    print(f"Time: {session.completed_at}")
    print(f"Test data keys: {list(session.test_data.keys()) if session.test_data else 'None'}")
    if session.test_data and 'questions' in session.test_data:
        print(f"Questions in data: {len(session.test_data['questions'])}")
    print("-" * 60)

# 测试 get_latest_session 方法
print("\n=== 测试 get_latest_session ===")
if sessions.exists():
    student_id = sessions.first().student_id
    latest = RecentPracticeSession.get_latest_session(student_id)
    if latest:
        print(f"✓ get_latest_session 工作正常")
        print(f"Student {student_id} 的最新会话: {latest.session_id}")
    else:
        print(f"✗ get_latest_session 返回 None")
else:
    print("没有数据可测试")
