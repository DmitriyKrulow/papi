// frontend/src/App.tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
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

// Компонент для защиты маршрутов (требуется авторизация)
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading } = useAuth();
  const token = localStorage.getItem('token');

  if (token) {
    return <>{children}</>;
  }
  
  if (!loading) {
    return <Navigate to="/login" replace />;
  }
  
  return null;
};

// Компонент для защиты админ-маршрутов (требуется роль admin)
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { loading, user } = useAuth();
  const token = localStorage.getItem('token');

  if (token && user && user.role === 'admin') {
    return <>{children}</>;
  }
  
  if (token && user && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  if (token) {
    return children;
  }
  
  if (!loading) {
    return <Navigate to="/login" replace />;
  }
  
  return null;
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
      </AuthProvider>
    </Router>
  );
}

export default App;