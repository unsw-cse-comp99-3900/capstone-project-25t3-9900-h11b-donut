from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Notification

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Notification
import json

@csrf_exempt
@require_POST
def mark_message_as_read(request, message_id):
    try:
        n = Notification.objects.get(id=message_id)
        n.is_read = True
        n.save()
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Message not found"}, status=404)

@csrf_exempt
@require_POST
def mark_messages_as_read(request):
    try:
        body = json.loads(request.body)
        ids = body.get("ids", [])

        if not ids:
            return JsonResponse({"success": False, "error": "ids required"}, status=400)

        Notification.objects.filter(id__in=ids).update(is_read=True)
        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@require_GET
def get_reminders(request, student_id):
    """获取用户所有提醒（按时间倒序）"""

    only_unread = request.GET.get("unread") == "1"

    qs = Notification.objects.filter(student_id=student_id)
    if only_unread:
        qs = qs.filter(is_read=False)

    qs = qs.order_by("-created_at")

    data = []
    for r in qs:
        data.append({
            "id": r.id,
            "type": r.message_type,
            "title": r.title,
            "preview": r.preview or "",
            "content": r.content or "",
            "createdAt": r.created_at.isoformat(),
            "dueTime": r.due_time.isoformat() if r.due_time else None,
            "isRead": r.is_read,
            "courseCode": r.course_code,
            "taskId": r.task_id,
        })

    return JsonResponse({"success": True, "data": data})
