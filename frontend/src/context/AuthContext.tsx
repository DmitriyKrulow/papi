// frontend/src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import axios, { AxiosError } from 'axios';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  role: string;
  is_active: boolean;
}

interface UserToken {
  access_token: string;
  token_type: string;
}

interface UserLogin {
  username: string;
  password: string;
}

interface UserRegister {
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  password: string;
}

interface UserProfile {
  username?: string;
  email?: string;
  full_name?: string;
  phone?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  token: string | null;
  register: (userData: UserRegister) => Promise<User>;
  login: (credentials: UserLogin) => Promise<UserToken>;
  logout: () => void;
  getToken: () => Promise<string | null>;
  getCurrentUser: () => Promise<User | null>;
  updateProfile: (profileData: UserProfile) => Promise<User>;
  changePassword: (oldPassword: string, newPassword: string) => Promise<boolean>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false); // Начальное состояние
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const register = useCallback(async (userData: UserRegister) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post<UserToken>('/api/auth/register', userData);
      const token = response.data.access_token;
      const meResponse = await axios.get<User>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUser(meResponse.data);
      setToken(token);
      localStorage.setItem('token', token);
      console.log('[Auth] Token saved to localStorage:', token.substring(0, 30) + '...');
      console.log('[Auth] localStorage.token after save:', localStorage.getItem('token')?.substring(0, 30) + '...');
      return meResponse.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (credentials: UserLogin) => {
    setLoading(true);
    setError(null);
    try {
      console.log('[Auth] Login called with username:', credentials.username);
      const response = await axios.post<UserToken>('/api/auth/login', credentials);
      console.log('[Auth] Login full response:', response);
      console.log('[Auth] Login response.data:', response.data);
      console.log('[Auth] Login response.data type:', typeof response.data);
      console.log('[Auth] Login response.data keys:', Object.keys(response.data));
      const token = response.data.access_token;
      console.log('[Auth] Extracted token:', token ? token.substring(0, 30) + '...' : 'NO TOKEN');
      console.log('[Auth] Token is string?', typeof token === 'string');
      console.log('[Auth] Token length:', token?.length);
      setToken(token);
      localStorage.setItem('token', token);
      console.log('[Auth] Login - Token saved to localStorage:', token.substring(0, 30) + '...');
      console.log('[Auth] Token in localStorage after save:', localStorage.getItem('token')?.substring(0, 30) + '...');
      console.log('[Auth] localStorage keys after save:', Object.keys(localStorage));
      
      const savedToken = localStorage.getItem('token');
      if (!savedToken) {
        console.error('[Auth] CRITICAL ERROR: Token not saved to localStorage!');
      } else if (savedToken !== token) {
        console.error('[Auth] CRITICAL ERROR: Token mismatch! Expected:', token.substring(0, 30) + '...', 'Got:', savedToken.substring(0, 30) + '...');
      } else {
        console.log('[Auth] ✅ Token verified in localStorage');
      }
      
      console.log('[Auth] About to call /api/auth/me with token:', token?.substring(0, 30) + '...');
      
      const meResponse = await axios.get<User>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      setUser(meResponse.data);
      localStorage.setItem('user', JSON.stringify(meResponse.data));
      
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      const errorDetail = axiosError.response?.data || axiosError.message || 'Login failed';
      setError(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }, []);

  const getToken = useCallback(async (): Promise<string | null> => {
    if (token) return token;
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      return storedToken;
    }
    return null;
  }, [token]);

  const getCurrentUser = useCallback(async (): Promise<User | null> => {
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setUser(null);
        return null;
      }
      const response = await axios.get<User>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      });
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      setUser(response.data);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      if (axiosError.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      }
      return null;
    }
  }, []);

  const updateProfile = useCallback(async (profileData: UserProfile) => {
    setLoading(true);
    setError(null);
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        throw new Error('Not authenticated');
      }
      const response = await axios.put<User>('/api/auth/profile', profileData, {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      });
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to update profile');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const changePassword = useCallback(async (oldPassword: string, newPassword: string) => {
    setLoading(true);
    setError(null);
    try {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        throw new Error('Not authenticated');
      }
      await axios.post('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      }, {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      });
      return true;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to change password');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // useEffect отключён — инициализация происходит только при login()
  // useEffect(() => {
  //   const initAuth = async () => {
  //     await getCurrentUser();
  //   };
  //   initAuth();
  // }, [getCurrentUser]);

  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      error,
      token,
      register,
      login,
      logout,
      getToken,
      getCurrentUser,
      updateProfile,
      changePassword,
      isAuthenticated: !!user,
      isAdmin,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};