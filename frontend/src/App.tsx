// frontend/src/App.tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetCreate from './pages/AssetCreate';
import AssetDetail from './pages/AssetDetail';
import AssetEdit from './pages/AssetEdit';
import Reports from './pages/Reports';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AdminPanel from './pages/AdminPanel';
import './index.css';

// Компонент для защиты маршрутов (требуется авторизация)
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// Компонент для защиты админ-маршрутов (требуется роль admin)
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  try {
    const user = userStr ? JSON.parse(userStr) : null;
    if (!user || user.role !== 'admin') {
      return <Navigate to="/dashboard" replace />;
    }
  } catch {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-gray-50">
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
      </AuthProvider>
    </Router>
  );
}

export default App;