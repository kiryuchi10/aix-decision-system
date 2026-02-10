import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

// Empty string = same-origin requests; Vite proxy in dev forwards /api to backend (avoids CORS).
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').toString().replace(/\/$/, '');
const BASE = API_BASE_URL === '' ? '' : API_BASE_URL;

interface User {
  id: number;
  email: string;
  role: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored token
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      // Fetch user info
      fetchUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (authToken: string) => {
    try {
      const response = await axios.get(`${BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const getDetailMessage = (error: any, fallback: string) => {
    if (!error.response) return 'Cannot reach server. Is the backend running?';
    const d = error.response?.data?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length > 0) return d[0]?.msg ?? String(d[0]);
    return fallback;
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${BASE}/api/v1/auth/login`, {
        email,
        password
      });
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUser(access_token);
    } catch (error: any) {
      const msg = getDetailMessage(error, 'Login failed');
      throw new Error(msg);
    }
  };

  const signup = async (email: string, password: string, fullName?: string) => {
    try {
      await axios.post(`${BASE}/api/v1/auth/signup`, {
        email,
        password,
        full_name: fullName
      });
      // Auto-login after signup
      await login(email, password);
    } catch (error: any) {
      throw new Error(getDetailMessage(error, 'Signup failed'));
    }
  };

  const demoLogin = async () => {
    try {
      const response = await axios.post(`${BASE}/api/v1/auth/demo-login`);
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUser(access_token);
    } catch (error: any) {
      throw new Error(getDetailMessage(error, 'Demo login failed'));
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        signup,
        demoLogin,
        logout,
        isAuthenticated: !!token && !!user,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
