import { useEffect } from 'react';
import type { ReactNode } from 'react';
//import apiService from '../services/api';

interface ProtectedRouteProps {
  children: ReactNode;
}
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const loginTime = parseInt(localStorage.getItem('login_time') || '0');
    const uid = localStorage.getItem('current_user_id');  // ✅ 新增
    const maxDuration = 1000 * 60 * 30; // 30分钟有效期（原来注释写15但计算是30）

    const expired = Date.now() - loginTime > maxDuration;

    // ✅ 增强：检测是否存在 current_user_id
    if (!token || expired || !uid) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('login_time');
      localStorage.removeItem('current_user_id'); // ✅ 新增清理
      localStorage.removeItem('user');
      window.location.hash = '#/signup';
    }
  }, []);

  // 再次检查
  const token = localStorage.getItem('auth_token');
  const loginTime = parseInt(localStorage.getItem('login_time') || '0');
  const uid = localStorage.getItem('current_user_id');  // ✅ 新增
  const maxDuration = 1000 * 60 * 30;
  const expired = Date.now() - loginTime > maxDuration;

  if (!token || expired || !uid) {
    return null;
  }

  return <>{children}</>;
}
