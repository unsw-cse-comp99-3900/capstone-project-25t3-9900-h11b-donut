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

        # 1️获取所有选课关系
        enrollments = StudentEnrollment.objects.all()

        for enroll in enrollments:
            student_id = enroll.student_id
            course_code = enroll.course_code

            # 2️获取课程任务
            tasks = CourseTask.objects.filter(course_code=course_code)

            for task in tasks:
                if not task.deadline:
                    continue
                # 把 DateField 转成当天 23:59 的完整时间，避免和 timezone.now() 类型不匹配 （后期可以考虑给 task加具体时间点）
                deadline_dt = datetime.combine(task.deadline, time(23, 59, 59)).astimezone(timezone.get_current_timezone())
                time_diff = deadline_dt - now
                hours_left = time_diff.total_seconds() / 3600

                # 3️ 检查学生进度  progress<100或者无记录都视为未完成 都会提醒
                progress = TaskProgress.objects.filter(student_id=student_id, task_id=task.id).first()
                is_completed = progress and progress.progress >= 100

                # 4️ 判断是否接近DDL
                if not is_completed and 0 < hours_left <= 24:
                    # 检查是否已经有提醒
                    exists = Notification.objects.filter(
                        student_id=student_id,
                        task_id=task.id,
                        message_type="due_alert"
                    ).exists()

                    if not exists:
                        # 生成提醒
                        msg_title = f"Task Due Soon"
                        msg_preview = f"Task '{task.title}' in course {course_code} is due in {int(hours_left)} hours."

                        Notification.objects.create(
                            student_id=student_id,
                            course_code=course_code,
                            task_id=task.id,
                            message_type="due_alert",
                            title=msg_title,
                            preview=msg_preview,
                            content=msg_preview,
                            due_time=task.deadline,
                        )
                        alerts_created += 1
                        self.stdout.write(
                            self.style.WARNING(f"[DueAlert] {student_id} - {task.title} ({int(hours_left)}h left)")
                        )

        if alerts_created:
            self.stdout.write(self.style.SUCCESS(f" 已生成 {alerts_created} 条提醒"))
        else:
            self.stdout.write(self.style.SUCCESS("暂无新的提醒生成"))
