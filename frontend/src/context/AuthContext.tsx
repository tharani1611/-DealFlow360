import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '../types';
import { authApi } from '../services/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  register: (payload: { organization_name: string; organization_slug: string; email: string; password: string; full_name?: string }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async () => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch {
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (newToken: string) => {
    localStorage.setItem('access_token', newToken);
    setToken(newToken);
    setIsLoading(true);
    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (err) {
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: { organization_name: string; organization_slug: string; email: string; password: string; full_name?: string }) => {
    setIsLoading(true);
    try {
      const response = await authApi.register(payload);
      await login(response.access_token);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser: fetchCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
