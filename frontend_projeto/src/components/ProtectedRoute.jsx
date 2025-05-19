import React, { useContext } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { authContext } from '../context/AuthContext'; 

function ProtectedRoute() {
  const { token, isLoading } = useContext(authContext); 

  if (isLoading) {
    return <div>A verificar autenticação...</div>; 
  }

  if (!token) { 
    return <Navigate to="/login" replace />; 
  }

  return <Outlet />; 
}

export default ProtectedRoute;