from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time 


from reminder.models import Notification

from courses.models import CourseTask, StudentEnrollment
from stu_accounts.models import StudentAccount
from task_progress.models import TaskProgress

#Put all the reminders into the notification database and wait for the student to log in to the frontend to request GET/app/reminders/<student_id>/push accurately based on the student ID
class Command(BaseCommand):
    help = "Automatically scan task DDL and generate reminders for unfinished students"

    def handle(self, *args, **options):
        now = timezone.now()
        alerts_created = 0

        # fixed notification time
        ALERT_OFFSETS = [2.983, 2.933, 2.883, 2.833, 2.783, 2.733]
        WINDOW_SEC = 90  
        DEDUP_MINUTES = 10  

        enrollments = StudentEnrollment.objects.all()

        for enroll in enrollments:
            student_id = enroll.student_id
            course_code = enroll.course_code

            tasks = CourseTask.objects.filter(course_code=course_code)

            for task in tasks:
                if not task.deadline:
                    continue

                # deadline : DateField，turn to today 23:59:59,datetime
                deadline_dt = datetime.combine(task.deadline, time(23, 59, 59)).astimezone(timezone.get_current_timezone())

                # remaining hour
                time_diff = deadline_dt - now
                hours_left = time_diff.total_seconds() / 3600

                # expire -> skip
                if hours_left <= 0:
                    continue

                # check done or not
                progress = TaskProgress.objects.filter(student_id=student_id, task_id=task.id).first()
                is_completed = progress and progress.progress >= 100
                if is_completed:
                    continue

                # fixed notifcation :24h、12h、2h
                for offset in ALERT_OFFSETS:
                    alert_time = deadline_dt - timedelta(hours=offset)
                    diff_sec = abs((alert_time - now).total_seconds())

                    # If the current time falls near the reminder point (± 90 seconds)
                    if diff_sec <= WINDOW_SEC:
                        # De duplication judgment: whether there is already a reminder of this type 10 minutes before and after the reminder time
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

                        # create notification
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
                            due_time=task.deadline,  
                        )
                        alerts_created += 1
                        self.stdout.write(
                            self.style.WARNING(f"[DueAlert {offset}h] {student_id} - {task.title}")
                        )

        if alerts_created:
            self.stdout.write(self.style.SUCCESS(f"generating {alerts_created} notifications"))
        else:
            self.stdout.write(self.style.SUCCESS("no new notifications"))
