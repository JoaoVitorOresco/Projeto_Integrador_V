import React, { createContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios'; 
import { useNavigate } from 'react-router-dom';


export const authContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [user, setUser] = useState(null);

  const [isLoading, setIsLoading] = useState(true); 
  const navigate = useNavigate();

  const fetchUserDetails = useCallback(async (currentToken) => {
    if (!currentToken) {
      setUser(null);
      setToken(null);
      localStorage.removeItem('authToken');
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true); 

    try {
      const response = await axios.get('/api/auth/user/', { 
        headers: {
          'Authorization': `Token ${currentToken}`
        }
      });
      setUser(response.data);
      console.log("AuthContext: Detalhes do usuário carregados:", response.data);
    } catch (error) {
      console.error("AuthContext: Falha ao buscar detalhes do usuário ou token inválido:", error);
      setUser(null);
      localStorage.removeItem('authToken');
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []); 

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken); 
      fetchUserDetails(storedToken);
    } else {
      setIsLoading(false); 
    }
  }, [fetchUserDetails]);

  const login = async (newToken, userDataFromLogin) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    setIsLoading(true); 

    if (userDataFromLogin) {
      setUser(userDataFromLogin);
      setIsLoading(false); 
      console.log("AuthContext: Usuário logado com dados da API de login:", userDataFromLogin);
    } else {
      await fetchUserDetails(newToken); 
    }
  };

  // Envolve logout em useCallback para estabilidade
  const logout = useCallback(() => { 
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    setIsLoading(false); 
    console.log("AuthContext: Usuário deslogado.");
    navigate('/login'); 
  }, [navigate]); 


  if (isLoading && token === null && localStorage.getItem('authToken')) {
     return <div>Carregando aplicação...</div>;
  }
  if (isLoading && token) { 
    return <div>A verificar sessão...</div>; 
  }

  return (
 
    <authContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token, isLoading }}>
      {children}
    </authContext.Provider>
  );
};
