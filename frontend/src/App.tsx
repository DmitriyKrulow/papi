// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './hooks/useTheme';
import { useAuth } from './hooks/useAuth';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetCreate from './pages/AssetCreate';
import AssetDetail from './pages/AssetDetail';
import AssetEdit from './pages/AssetEdit';
import Reports from './pages/Reports';
import Inventory from './pages/Inventory';
import Marking from './pages/Marking';
import RepairList from './pages/RepairList';
import RepairCreate from './pages/RepairCreate';
import RepairEdit from './pages/RepairEdit';
import Login from './pages/Login';
import Register from './pages/Register';
import PasswordReset from './pages/PasswordReset';
import Profile from './pages/Profile';
import AdminPanel from './pages/AdminPanel';
import InventoryMobile from './pages/InventoryMobile';
import InventoryAssetMobile from './pages/InventoryAssetMobile';
import AuditLog from './pages/AuditLog';
import NotificationsPage from './pages/NotificationsPage';
import './index.css';

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    // Логгируем ошибку в консоль для разработчиков, но не показываем stack trace пользователю
    console.error('[ErrorBoundary] Application error:', error);
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="text-center p-8 max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Что-то пошло не так</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Приложение столкнулось с непредвиденной ошибкой. Попробуйте перезагрузить страницу.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Перезагрузить страницу
              </button>
            </div>
            {/* Скрываем детальную информацию для безопасности */}
            <details className="mt-6 text-left text-xs text-gray-400 dark:text-gray-600">
              <summary className="cursor-pointer hover:text-gray-600 dark:hover:text-gray-400">
                Для разработчиков
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded overflow-auto max-h-32">
                {this.state.error?.message}
              </pre>
            </details>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Компонент для защиты маршрутов (требуется авторизация)
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, token, isAuthenticated } = useAuth();

  // Если всё ещё загружается — показываем спиннер
  if (loading) {
    return <div className="flex justify-center items-center py-12"><div className="text-gray-500">⏳ Загрузка...</div></div>;
  }
  
  // Если авторизован — показываем контент
  if (isAuthenticated) {
    return <>{children}</>;
  }
  
  // Иначе редиректим на логин
  return <Navigate to="/login" replace />;
};

// Компонент для защиты админ-маршрутов (требуется роль admin)
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, user, token, isAuthenticated } = useAuth();

  // Если всё ещё загружается — показываем спиннер
  if (loading) {
    return <div className="flex justify-center items-center py-12"><div className="text-gray-500">⏳ Загрузка...</div></div>;
  }
  
  // Если не авторизован — редиректим на логин
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  // Если авторизован, но не админ — редиректим на дашборд
  if (user && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  // Если админ — показываем контент
  return <>{children}</>;
};

function App() {
  return (
    <ErrorBoundary>
    <Router>
      <AuthProvider>
        <ThemeProvider>
          <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <main className="flex-grow container mx-auto px-4 py-8">
              <Routes>
                {/* Публичные маршруты (доступны без авторизации) */}
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/password-reset" element={<PasswordReset />} />
                
                {/* Защищенные маршруты (требуется авторизация) */}
                <Route path="/dashboard" element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                } />
                <Route path="/assets" element={
                  <PrivateRoute>
                    <Assets />
                  </PrivateRoute>
                } />
                <Route path="/assets/create" element={
                  <PrivateRoute>
                    <AssetCreate />
                  </PrivateRoute>
                } />
                <Route path="/assets/:id" element={
                  <PrivateRoute>
                    <AssetDetail />
                  </PrivateRoute>
                } />
                <Route path="/assets/:id/edit" element={
                  <PrivateRoute>
                    <AssetEdit />
                  </PrivateRoute>
                } />
<Route path="/reports" element={
                  <PrivateRoute>
                    <Reports />
                  </PrivateRoute>
                } />
                <Route path="/inventory" element={
                  <PrivateRoute>
                    <Inventory />
                  </PrivateRoute>
                } />
                <Route path="/inventory-mobile" element={
                  <PrivateRoute>
                    <InventoryMobile />
                  </PrivateRoute>
                } />
                <Route path="/inventory/asset/:assetId" element={
                  <PrivateRoute>
                    <InventoryAssetMobile />
                  </PrivateRoute>
                } />
                <Route path="/marking" element={
                  <PrivateRoute>
                    <Marking />
                  </PrivateRoute>
                } />
                
                {/* Маршруты для заявок на ремонт */}
                <Route path="/repairs" element={
                  <PrivateRoute>
                    <RepairList />
                  </PrivateRoute>
                } />
                <Route path="/repairs/create" element={
                  <PrivateRoute>
                    <RepairCreate />
                  </PrivateRoute>
                } />
                <Route path="/repairs/:id" element={
                  <PrivateRoute>
                    <RepairEdit />
                  </PrivateRoute>
                } />
                <Route path="/repairs/:id/edit" element={
                  <PrivateRoute>
                    <RepairEdit />
                  </PrivateRoute>
                } />
                <Route path="/profile" element={
                  <PrivateRoute>
                    <Profile />
                  </PrivateRoute>
                } />
                
                {/* Админ-маршрут (требуется роль admin) */}
                <Route path="/admin" element={
                  <AdminRoute>
                    <AdminPanel />
                  </AdminRoute>
                } />
                
                {/* Журнал аудита (только админ) */}
                <Route path="/audit" element={
                  <AdminRoute>
                    <AuditLog />
                  </AdminRoute>
                } />
                
                {/* Уведомления */}
                <Route path="/notifications" element={
                  <PrivateRoute>
                    <NotificationsPage />
                  </PrivateRoute>
                } />
                
                {/* 404 - перенаправление на главную */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </ThemeProvider>
      </AuthProvider>
    </Router>
    </ErrorBoundary>
  );
}

export default App;