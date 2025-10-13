import { useEffect } from 'react';
import type { ReactNode } from 'react';   
import apiService from '../services/api';
interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  useEffect(() => {
    // 如果没有登录，就跳回登录页
    if (!apiService.isAuthenticated()) {
      window.location.hash = '#/login-student';
    }
  }, []);

  return <>{children}</>;
}
