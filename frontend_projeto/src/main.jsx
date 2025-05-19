// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { AuthProvider } from './context/AuthContext.jsx'; // Usando authContext
import { BrowserRouter } from 'react-router-dom'; // Importar BrowserRouter
import './index.css'; 

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>   {/* BrowserRouter envolve AuthProvider */}
      <AuthProvider>  {/* AuthProvider está DENTRO do BrowserRouter */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);