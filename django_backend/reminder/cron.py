from django.utils import timezone
from datetime import timedelta
from courses.models import CourseTask, StudentEnrollment
from .models import Notification
from django.utils import timezone
timezone.activate("Australia/Sydney")  
from django.utils import timezone
from plans.models import StudyPlanItem
from reminder.models import Notification

def check_daily_overdue():
    """
    每天固定澳洲时间 13:00 检查未完成的 study_plan_item
    并写入 daily_overdue 通知
    """
    print(">>> DAILY OVERDUE CRON IS RUNNING")

    sydney_tz = timezone.get_fixed_timezone(600)
    now = timezone.now().astimezone(sydney_tz)

    # if not (now.hour == 17 and now.minute < 27):
    #     return
    # 测试：只要当前 minute % 5 == 0 就执行一次
    if now.minute % 5 != 0:
        return

    print(">>> DAILY OVERDUE CRON IS RUNNING111")

    today = now.date()

    overdue_items = StudyPlanItem.objects.filter(
        scheduled_date=today,
        completed=False
    )
    print("Found overdue_items:", overdue_items.count())

    for item in overdue_items:
        print(f"  Processing item {item.id} for student {item.plan.student_id}")

        student_id = item.plan.student_id
        task_id = item.task_id

        Notification.objects.get_or_create(
            student_id=student_id,
            task_id=task_id,
            message_type="nightly_notice",
            defaults={
                "title": "今日学习任务未完成提醒",
                "preview": f"{item.course_title} - 第 {item.part_index+1}/{item.parts_count} 部分未完成",
                "content": (
                    f"你的任务 [{item.part_title}] 未完成，已自动顺延到明天。"
                ),
                "due_time": item.scheduled_date,
            }
        )

def check_due_tasks():
    now = timezone.localtime()
    print("=== CRON NOW (localtime) ===", now)

    alert_hours = [24, 12, 2, 1]

    # 先拿所有未来一点点的任务（防止历史任务干扰）
    all_tasks = CourseTask.objects.filter(
        deadline__gte=timezone.now() - timedelta(days=1)
    )

    # 打印所有任务的本地时间
    print("=== ALL TASK DEADLINES (local) ===")
    for t in all_tasks:
        ld = timezone.localtime(t.deadline)
        diff_min = (ld - now).total_seconds() / 60
        print(f"  Task {t.id} {t.course_code} {t.title} -> {ld}  (diff={diff_min:.1f} min)")

    for hours in alert_hours:
        center = now + timedelta(hours=hours)
        window_start = center - timedelta(minutes=2, seconds=30)
        window_end   = center + timedelta(minutes=2, seconds=30)

        print(f"\n--- {hours}h window (symmetric) ---")
        print("  window_start:", window_start)
        print("  window_end  :", window_end)


        count = 0

        for task in all_tasks:
            local_deadline = timezone.localtime(task.deadline)

            if window_start <= local_deadline < window_end:
                count += 1
                print(f"  [MATCH {hours}h] Task {task.id} -> {local_deadline}")

                # 发提醒（这里逻辑你可以先保留不动）
                enrolled = StudentEnrollment.objects.filter(course_code=task.course_code)
                for e in enrolled:
                    msg_type = f"due_{hours}h"
                    if Notification.objects.filter(
                        student_id=e.student_id,
                        task_id=task.id,
                        message_type=msg_type
                    ).exists():
                        continue

                    Notification.objects.create(
                        student_id=e.student_id,
                        course_code=task.course_code,
                        task_id=task.id,
                        message_type=msg_type,
                        title=f"Task '{task.title}' is due in {hours}h",
                        preview=f"The task '{task.title}' for course {task.course_code} will be due in {hours} hours.",
                        content=f"Your task '{task.title}' in course {task.course_code}' is due soon (in {hours}h).",
                        due_time=task.deadline,
                    )

        print(f"[CHECK]{hours}h-window tasks = {count}")

    print("[✔] check_due_tasks finished.")