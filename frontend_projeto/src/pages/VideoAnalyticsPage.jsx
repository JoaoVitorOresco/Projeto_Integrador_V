import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Spinner, Alert, Button } from 'react-bootstrap';
import { authContext } from '../context/AuthContext';
import { ArrowLeftCircle, AlertCircle, ImageOff } from 'lucide-react'; 
import styles from './VideoAnalyticsPage.module.css'; 

function VideoAnalyticsPage() {
  const { videoId } = useParams(); 
  const { token, logout } = useContext(authContext); 
  const navigate = useNavigate(); 
  
  const [graphs, setGraphs] = useState(null); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoTitle, setVideoTitle] = useState(''); 

  // URL base do seu backend Django (ajuste se necessário)
  const BACKEND_URL = 'http://localhost:8001'; // Se precisar buscar título do vídeo

  useEffect(() => {
    if (!videoId) {
        setError("ID do vídeo não encontrado na URL.");
        setLoading(false);
        return;
    }
    if (!token) {
        setError("Autenticação necessária. Por favor, faça login.");
        setLoading(false); 
        navigate('/login'); 
        return;
    }

    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      setGraphs(null); 
      
      try {
         const videoInfoResponse = await fetch(`/api/mmpose/videos/${videoId}/`, { headers: { 'Authorization': `Token ${token}` }});
         if (videoInfoResponse.ok) {
           const videoData = await videoInfoResponse.json();
           setVideoTitle(videoData.title || `Vídeo #${videoId}`);
         } else {
           setVideoTitle(`Vídeo #${videoId}`); // Fallback
         }
       } catch (e) {
         console.warn("Não foi possível buscar o título do vídeo", e);
         setVideoTitle(`Vídeo #${videoId}`);
       }


      try {
        const apiUrl = `/api/mmpose/videos/${videoId}/analytics/`; 

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
              errorMsg = "Não autorizado ou sessão expirada. Faça login novamente.";
              if (logout) logout(); // Chama logout do contexto se disponível
              navigate('/login');
          } else {
              try {
                  const errorData = await response.json();
                  errorMsg = errorData.detail || errorData.error || JSON.stringify(errorData);
              } catch(e) { /* Ignora erro ao fazer parse */ }
          }
          throw new Error(errorMsg);
        }

        const data = await response.json();
        
        if (!data || Object.keys(data).length === 0 || Object.values(data).every(value => value === null)) {
            setError("Nenhum gráfico pôde ser gerado para este vídeo ou os dados estão vazios. Verifique se o processamento foi concluído com sucesso e gerou dados de análise.");
            setGraphs(null);
        } else {
            setGraphs(data);
        }
      } catch (err) {
        console.error("Erro ao buscar análises:", err);
        setError(err.message || "Falha ao carregar os gráficos.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();

  }, [videoId, token, navigate, logout]); 

  const formatGraphTitle = (key) => {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className={styles.pageWrapper}>
        <Container className={`py-4 text-center ${styles.pageContainer}`}>
          <Spinner animation="border" variant="primary" className={styles.spinner} />
          <p className={`mt-3 ${styles.loadingText}`}>Carregando análises do vídeo...</p>
        </Container>
      </div>
    );
  }

  return (
    <div className={styles.pageWrapper}>
      {/* Navbar similar à VideoListPage para consistência, se desejar */}
      <nav className={`navbar navbar-expand-lg ${styles.navbar}`}>
        <Container>
          <Link className={`navbar-brand ${styles.navbarBrand}`} to="/video-list">
            Esgrimetrics Análises
          </Link>
          <Button variant="outline-light" onClick={() => navigate('/video-list')} className={styles.navButton}>
            <ArrowLeftCircle size={20} className="me-2" /> Voltar para Lista
          </Button>
        </Container>
      </nav>

      <Container className={`py-4 ${styles.pageContainer}`}>
        <Row className="mb-4 align-items-center">
          <Col>
            <h2 className={styles.pageTitle}>Análises do Vídeo {videoTitle || `#${videoId}`}</h2>
          </Col>
        </Row>

        {error && (
          <Alert variant="danger" className={styles.alertBox}>
            <AlertCircle size={24} className="me-2"/>
            <strong>Erro ao carregar gráficos:</strong> {error}
          </Alert>
        )}

        {graphs && !loading && !error && Object.keys(graphs).length > 0 && (
          <Row xs={1} md={2} className="g-4">
            {Object.entries(graphs).map(([key, base64Image]) => (
              <Col key={key}>
                <Card className={`${styles.graphCard} h-100`}>
                  <Card.Header as="h5" className={styles.cardHeader}>
                    {formatGraphTitle(key)} 
                  </Card.Header>
                  <Card.Body className={`text-center d-flex align-items-center justify-content-center ${styles.cardBody}`}>
                    {base64Image ? ( 
                      <img 
                        src={base64Image} 
                        alt={`Gráfico ${formatGraphTitle(key)}`}
                        className="img-fluid" 
                        style={{ maxWidth: '100%', height: 'auto', borderRadius: 'var(--border-radius-sm)' }}
                      />
                    ) : (
                      <div className="text-muted">
                        <ImageOff size={48} className="mb-2" />
                        <p>Gráfico não disponível.</p>
                      </div>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {!graphs && !loading && !error && (
           <Alert variant="info" className={styles.alertBox}>
             <AlertCircle size={24} className="me-2"/>
             Nenhum gráfico disponível ou dados insuficientes para gerar as análises deste vídeo.
           </Alert>
        )}
      </Container>
    </div>
  );
}

export default VideoAnalyticsPage;