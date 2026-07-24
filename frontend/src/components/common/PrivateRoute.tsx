// frontend/src/components/common/PrivateRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';

interface PrivateRouteProps {
  requiredRole?: string;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ requiredRole }) => {
  // Получаем данные из localStorage
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  // Если нет токена - редирект на логин
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Если требуется роль и она не совпадает - редирект на главную
  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default PrivateRoute;