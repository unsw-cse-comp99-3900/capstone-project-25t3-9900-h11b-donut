from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time 

# 自己的模型
from reminder.models import Notification

# 其他 app 模型（根据你的实际路径）
from courses.models import CourseTask, StudentEnrollment
from stu_accounts.models import StudentAccount
from task_progress.models import TaskProgress

#把所有要提醒的放入notification数据库 等待学生登陆 前端请求GET /api/reminders/<student_id>/ 根据学生id精准推送
class Command(BaseCommand):
    help = "自动扫描任务DDL并为未完成学生生成提醒"

    def handle(self, *args, **options):
        now = timezone.now()
        alerts_created = 0

        # 固定提醒时间点（单位：小时）
        ALERT_OFFSETS = [3.85,  3.70,3.67, 3.50]
        WINDOW_SEC = 90  # 容错窗口（防止错过）
        DEDUP_MINUTES = 10  # 去重窗口

        enrollments = StudentEnrollment.objects.all()

        for enroll in enrollments:
            student_id = enroll.student_id
            course_code = enroll.course_code

            tasks = CourseTask.objects.filter(course_code=course_code)

            for task in tasks:
                if not task.deadline:
                    continue

                # deadline 是 DateField，转换为当天23:59:59的 datetime
                deadline_dt = datetime.combine(task.deadline, time(23, 59, 59)).astimezone(timezone.get_current_timezone())

                # 计算剩余时间
                time_diff = deadline_dt - now
                hours_left = time_diff.total_seconds() / 3600

                # 已经过期跳过
                if hours_left <= 0:
                    continue

                # 检查学生是否已完成
                progress = TaskProgress.objects.filter(student_id=student_id, task_id=task.id).first()
                is_completed = progress and progress.progress >= 100
                if is_completed:
                    continue

                # 针对三个固定提醒点：24h、12h、2h
                for offset in ALERT_OFFSETS:
                    alert_time = deadline_dt - timedelta(hours=offset)
                    diff_sec = abs((alert_time - now).total_seconds())

                    # 如果当前时间落在提醒点附近（±90秒）
                    if diff_sec <= WINDOW_SEC:
                        # 去重判断：在提醒时间前后10分钟是否已有该类型提醒
                        dedup_start = alert_time - timedelta(minutes=DEDUP_MINUTES)
                        dedup_end = alert_time + timedelta(minutes=DEDUP_MINUTES)

                        exists = Notification.objects.filter(
                            student_id=student_id,
                            task_id=task.id,
                            message_type="due_alert",
                            created_at__gte=dedup_start,
                            created_at__lte=dedup_end
                        ).exists()

                        if exists:
                            continue

                        # 创建提醒
                        msg_title = f"Task due in {offset}h"
                        msg_preview = f"Task '{task.title}' in course {course_code} is due in {offset} hours."

                        Notification.objects.create(
                            student_id=student_id,
                            course_code=course_code,
                            task_id=task.id,
                            message_type="due_alert",
                            title=msg_title,
                            preview=msg_preview,
                            content=msg_preview,
                            due_time=task.deadline,  # 保持你的字段不改
                        )
                        alerts_created += 1
                        self.stdout.write(
                            self.style.WARNING(f"[DueAlert {offset}h] {student_id} - {task.title}")
                        )

        if alerts_created:
            self.stdout.write(self.style.SUCCESS(f"已生成 {alerts_created} 条提醒"))
        else:
            self.stdout.write(self.style.SUCCESS("暂无新的提醒生成"))
