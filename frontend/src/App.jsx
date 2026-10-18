import React, { createContext, useContext, useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import AdminPage from './pages/AdminPage';

export const AuthContext = createContext();

const ProtectedRoute = ({ children, requiredRole }) => {
  const { token, role } = useContext(AuthContext);
  if (!token) return <Navigate to="/login" replace />;
  if (requiredRole) {
    const isAuthorized = role === requiredRole || (requiredRole === 'admin' && role === 'super_admin');
    if (!isAuthorized) return <Navigate to="/chat" replace />;
  }
  return children;
};

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [role, setRole] = useState(localStorage.getItem('role'));
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const navigate = useNavigate();

  const login = (newToken, newRole, userData = null) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('role', newRole);
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    }
    setToken(newToken);
    setRole(newRole);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user');
    setToken(null);
    setRole(null);
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ token, role, user, login, logout }}>
      <Routes>
        <Route path="/" element={<Navigate to={token ? "/chat" : "/login"} replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/chat" element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute requiredRole="admin">
            <AdminPage />
          </ProtectedRoute>
        } />
      </Routes>
    </AuthContext.Provider>
  );
}
