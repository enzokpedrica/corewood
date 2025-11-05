import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Configurar axios com token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('token');
    }
  }, [token]);

  // Verificar se tem token ao carregar
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          // Verificar se token é válido fazendo uma requisição
          await axios.get(`${process.env.REACT_APP_API_URL || 'https://corewood.onrender.com'}/`);
          setLoading(false);
        } catch (error) {
          console.error('Token inválido:', error);
          logout();
        }
      } else {
        setLoading(false);
      }
    };
    checkAuth();
  }, [token]);

  const login = async (username, password) => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'https://corewood.onrender.com'}/auth/login`,
        formData
      );

      const { access_token } = response.data;
      setToken(access_token);
      setUser({ username });
      return { success: true };
    } catch (error) {
      console.error('Erro no login:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Erro ao fazer login'
      };
    }
  };

  const register = async (email, username, password, fullName) => {
    try {
      await axios.post(
        `${process.env.REACT_APP_API_URL || 'https://corewood.onrender.com'}/auth/register`,
        {
          email,
          username,
          password,
          full_name: fullName
        }
      );
      return { success: true };
    } catch (error) {
      console.error('Erro no registro:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Erro ao registrar'
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};