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
    """标记单条消息为已读"""
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
    """批量标记消息为已读"""
    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])
        Notification.objects.filter(id__in=ids).update(is_read=True)
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

@require_GET
def get_reminders(request, student_id):
    reminders = Notification.objects.filter(student_id=student_id).order_by('-created_at')

    data = []
    for r in reminders:
        created_at_str = (
            timezone.localtime(r.created_at).strftime("%Y-%m-%dT%H:%M:%S")
            if r.created_at else None
        )
        due_time_str = (
            timezone.localtime(r.due_time).strftime("%Y-%m-%dT%H:%M:%S")
            if r.due_time else None
        )
        data.append({
            "id": str(r.id), 
            "type": r.message_type,
            "title": r.title,
            "preview": r.preview or (r.content[:100] if r.content else ""),
            "timestamp": created_at_str,
            "isRead": getattr(r, "is_read", False),
            "courseId": r.course_code,
            "dueTime": due_time_str,
        })
    print("📬 Reminders for", student_id, "=>", data)

    return JsonResponse({"success": True, "data": data})

