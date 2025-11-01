export type MessageType = 'due_alert' | 'nightly_notice' | 'weekly_bonus' | 'system_notification';

export interface Message {
  id: string;
  type: MessageType;
  title: string;
  preview: string;
  timestamp: string;
  isRead: boolean;
  courseId?: string;
  dueTime?: string;
}

export const MESSAGE_TYPES: Record<MessageType, { label: string; icon: string }> = {
  due_alert: { label: 'Due Alerts', icon: '⏰' },
  nightly_notice: { label: 'Nightly Notices', icon: '❗' },
  weekly_bonus: { label: 'Weekly Bonuses', icon: '🏆' },
  system_notification: { label: 'System Notifications', icon: '🔔' },
};