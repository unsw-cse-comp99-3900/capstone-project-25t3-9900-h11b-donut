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
    const maxDuration = 1000 * 60 * 15; // 30分钟有效期（你可以改成1小时：1000*60*60）

    const expired = Date.now() - loginTime > maxDuration;

    //  如果没登录或已过期，就清空并跳回登录页
    if (!token || expired) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      localStorage.removeItem('login_time');
      window.location.hash = '#/signup';
    }
  }, []);

  //  再次检查：没登录就不渲染页面
  const token = localStorage.getItem('auth_token');
  const loginTime = parseInt(localStorage.getItem('login_time') || '0');
  const maxDuration = 1000 * 60 * 15;
  const expired = Date.now() - loginTime > maxDuration;

  if (!token || expired) {
    return null;
  }

  return <>{children}</>;
}