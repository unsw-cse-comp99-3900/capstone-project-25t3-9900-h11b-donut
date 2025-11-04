from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ChatConversation(models.Model):
    """对话会话模型 - 存储用户的对话历史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now=True)  # 用户最后活动时间
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user.username}"

class ChatMessage(models.Model):
    """聊天消息模型"""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # 可选的结构化数据
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class UserStudyPlan(models.Model):
    """用户学习计划存储 - 用于AI对话中的计划解释"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    plan_data = models.JSONField()  # 存储完整的AI生成计划数据
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # 标记当前活跃的计划
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Study Plan for {self.user.username} - {self.created_at.date()}"
    
    @classmethod
    def cleanup_old_plans(cls):
        """清理7天前的旧计划"""
        cutoff_date = timezone.now() - timedelta(days=7)
        cls.objects.filter(created_at__lt=cutoff_date).delete()

# 自动清理旧数据的管理器
class ChatManager:
    @staticmethod
    def cleanup_old_conversations():
        """清理7天前的对话记录"""
        cutoff_date = timezone.now() - timedelta(days=7)
        ChatConversation.objects.filter(created_at__lt=cutoff_date).delete()