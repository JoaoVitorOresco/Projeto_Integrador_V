import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import UploadVideo from './pages/UploadVideo';
import VideoListPage from './pages/VideoListPage'; 
import VideoAnalyticsPage from './pages/VideoAnalyticsPage'; 
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import './App.css';
import axios from 'axios';


function App() {
  return (
      <Routes>
        {/* Rotas Públicas */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/cadastro" element={<RegistrationPage />} />

        {/* Rotas Protegidas */}
        <Route element={<ProtectedRoute />}> {/* Protege todas as rotas aninhadas */}
          <Route path="/upload" element={<UploadVideo />} />
          <Route path="/video-list" element={<VideoListPage />} /> {/* <-- Rota para a lista */}
          <Route path="/videos/:videoId/analytics" element={<VideoAnalyticsPage />} /> {/* <-- Rota para análise */}
        </Route>

        {/* Rota para lidar com caminhos não encontrados */}
        {/* <Route path="*" element={<NotFoundPage />} /> */}

      </Routes>
  );
}

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.withCredentials = true;

export default App;