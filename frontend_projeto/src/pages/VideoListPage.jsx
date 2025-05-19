import React, { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Spinner, Alert, Button, ListGroup } from 'react-bootstrap';
import { authContext } from '../context/AuthContext';
import { Upload, LogOut } from 'lucide-react';

function VideoListPage() {

  const { token, logout } = useContext(authContext); 
  const navigate = useNavigate();
  
  const [videos, setVideos] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/login'); 
      return;
    }

    const fetchVideos = async () => {
      setLoading(true);
      setError(null);
      setVideos([]); 

      try {
        const apiUrl = '/api/mmpose/videos/'; 

        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          let errorMsg = `Erro ${response.status}: ${response.statusText}`;
           if (response.status === 401 || response.status === 403) {
             errorMsg = "Sessão inválida ou expirada. Faça login novamente.";
             if (logout) logout(); 
             navigate('/login');
          } else {
              try {
                  const errorData = await response.json();
                  errorMsg = errorData.detail || JSON.stringify(errorData);
              } catch(e) { /* Ignora erro */ }
          }
          throw new Error(errorMsg);
        }

        const data = await response.json();
        data.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
        setVideos(data);

      } catch (err) {
        console.error("Erro ao buscar vídeos:", err);
        setError(err.message || "Falha ao carregar a lista de vídeos.");
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();

  // Adiciona logout como dependência se ele puder mudar (geralmente não muda, mas é boa prática)
  }, [token, navigate, logout]); 

  // Função para lidar com o clique no botão de logout
  const handleLogout = () => {
    if (logout) {
      logout(); // Chama a função logout do AuthContext
    }
    navigate('/login'); // Redireciona para a página de login
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Data indisponível';
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
  };

  // Se estiver carregando e ainda não houver erro ou token inválido detectado no useEffect
  if (loading && !error && token) {
    return (
       <Container className="mt-4 text-center">
         <Spinner animation="border" role="status">
           <span className="visually-hidden">Carregando vídeos...</span>
         </Spinner>
         <p className="mt-2">A carregar vídeos...</p>
       </Container>
    );
  }
  
  // Se houver erro ou o token for inválido (redirecionamento já iniciado no useEffect)
  if (error || !token) {
     return (
       <Container className="mt-4">
          <Alert variant="danger">{error || "Autenticação necessária."}</Alert>
          {/* Opcional: Botão para ir para login se o redirecionamento automático falhar */}
          {!token && <Button onClick={() => navigate('/login')}>Ir para Login</Button>}
       </Container>
     );
  }


  // Renderização principal se carregado, sem erros e com token
  return (
    <Container className="mt-4">
      <Row className="mb-3 align-items-center">
        <Col>
          <h2>Meus Vídeos</h2>
        </Col>
        <Col xs="auto" className="d-flex">
          {/* Botão Upload */}
          <Button variant="primary" onClick={() => navigate('/upload')} className="me-2">
            <Upload size={18} className="me-1" /> Enviar Novo Vídeo
          </Button>
          {/* Botão Logout */}
          <Button variant="outline-danger" onClick={handleLogout}>
             <LogOut size={18} className="me-1" /> Sair
          </Button>
        </Col>
      </Row>

      {videos.length === 0 && (
        <Row>
          <Col>
            <Alert variant="info">Você ainda não enviou nenhum vídeo.</Alert>
          </Col>
        </Row>
      )}

      {videos.length > 0 && (
        <ListGroup>
          {videos.map(video => (
            <ListGroup.Item key={video.id} className="d-flex justify-content-between align-items-center flex-wrap">
              <div>
                <h5 className="mb-1">{video.title || `Vídeo ${video.id}`}</h5>
                <small className="text-muted">Enviado em: {formatDate(video.uploaded_at)}</small>
                <br/>
                <small className="text-muted">Estado: {video.processing_status || 'N/A'}</small>
              </div>
              <div className="mt-2 mt-md-0"> 
                 <Link to={`/videos/${video.id}/analytics`}>
                   <Button 
                     variant="outline-info" 
                     size="sm" 
                     className="me-2"
                     disabled={video.processing_status !== 'completed'} 
                     title={video.processing_status !== 'completed' ? 'Processamento não concluído' : 'Ver Análise'}
                   >
                     Ver Análise
                   </Button>
                 </Link>
                 {video.processed_video_url && (
                    <Button 
                        variant="outline-success" 
                        size="sm" 
                        href={video.processed_video_url} 
                        target="_blank" 
                        download 
                    >
                        Baixar Processado
                    </Button>
                 )}
              </div>
            </ListGroup.Item>
          ))}
        </ListGroup>
      )}
    </Container>
  );
}

export default VideoListPage;
