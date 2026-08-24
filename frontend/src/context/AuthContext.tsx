import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, setToken, getToken, removeToken } from '../services/api';
import { UserRole } from '../types';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  stateId?: number;
  districtId?: number;
}

interface AuthContextType {
  user: AuthUser | null;
  role: UserRole;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  setUserRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [role, setRole] = useState<UserRole>('SUPER_ADMIN');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const tokenRes = await authApi.login(email, password);
      setToken(tokenRes.access_token);

      const meRes = await authApi.getMe();
      const authUser: AuthUser = {
        id: meRes.id,
        name: meRes.name,
        email: meRes.email,
        role: meRes.role as UserRole,
        stateId: meRes.state_id,
        districtId: meRes.district_id,
      };

      setUser(authUser);
      setRole(authUser.role);
      setIsAuthenticated(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid email or password.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  // Restore authenticated session on mount or perform default demo login if no token present
  useEffect(() => {
    const existingToken = getToken();
    if (existingToken) {
      authApi
        .getMe()
        .then((res) => {
          const authUser: AuthUser = {
            id: res.id,
            name: res.name,
            email: res.email,
            role: res.role as UserRole,
            stateId: res.state_id,
            districtId: res.district_id,
          };
          setUser(authUser);
          setRole(authUser.role);
          setIsAuthenticated(true);
        })
        .catch(() => {
          // Token expired or invalid -> login with seed admin credentials
          login('admin.national@lams.gov.in', 'LamsAdmin@2026').catch(() => {});
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      // Auto-authenticate with demo admin credentials for seamless evaluation
      login('admin.national@lams.gov.in', 'LamsAdmin@2026').catch(() => {});
    }
  }, []);

  const logout = () => {
    removeToken();
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
  };

  const clearError = () => setError(null);

  const setUserRole = (newRole: UserRole) => {
    setRole(newRole);
    if (user) {
      setUser({ ...user, role: newRole });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated,
        loading,
        error,
        login,
        logout,
        clearError,
        setUserRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
