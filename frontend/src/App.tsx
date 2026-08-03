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
import RepairList from './pages/RepairList';
import RepairCreate from './pages/RepairCreate';
import RepairEdit from './pages/RepairEdit';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AdminPanel from './pages/AdminPanel';
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
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-red-50">
          <div className="text-center p-8">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Ошибка приложения</h1>
            <p className="text-gray-700 mb-4">{this.state.error?.message}</p>
            <pre className="bg-white p-4 rounded text-left text-sm overflow-auto max-w-2xl">
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Перезагрузить
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Компонент для защиты маршрутов (требуется авторизация)
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, token } = useAuth();

  if (token) {
    return <>{children}</>;
  }
  
  if (loading) {
    return <div className="flex justify-center items-center py-12"><div className="text-gray-500">⏳ Загрузка...</div></div>;
  }
  
  return <Navigate to="/login" replace />;
};

// Компонент для защиты админ-маршрутов (требуется роль admin)
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, user, token } = useAuth();

  if (token && user && user.role === 'admin') {
    return <>{children}</>;
  }
  
  if (token && user && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  if (token) {
    return <>{children}</>;
  }
  
  if (loading) {
    return <div className="flex justify-center items-center py-12"><div className="text-gray-500">⏳ Загрузка...</div></div>;
  }
  
  return <Navigate to="/login" replace />;
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