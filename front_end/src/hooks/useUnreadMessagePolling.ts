import { useEffect } from 'react'
import apiService from '../services/api'

export default function useUnreadMessagePolling(setUnreadMessageCount: (n: number) => void) {

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const messages = await apiService.getMessages();
        const unread = messages.filter(m => !m.isRead).length;
        setUnreadMessageCount(unread);
      } catch (e) {
        console.error('Failed to poll unread messages:', e);
      }
    }

    fetchCount(); // 页面加载时立即执行
    const timer = setInterval(fetchCount, 30000); // 每 30s 执行一次

    return () => clearInterval(timer); // 页面卸载时清除定时器
  }, [setUnreadMessageCount]);
}
