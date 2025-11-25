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

    fetchCount(); // Execute immediately upon page loading

    const timer = setInterval(fetchCount, 30000); // execute every 30s

    return () => clearInterval(timer); // Clear timer during page uninstallation

  }, [setUnreadMessageCount]);
}
