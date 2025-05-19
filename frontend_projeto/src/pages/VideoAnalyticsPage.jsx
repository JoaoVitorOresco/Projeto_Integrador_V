import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Spinner, Alert, Button } from 'react-bootstrap';
import { authContext } from '../context/AuthContext';

function VideoAnalyticsPage() {
  const { videoId } = useParams(); 
  const { token } = useContext(authContext); 
  const navigate = useNavigate(); 
  
  const [graphs, setGraphs] = useState(null); 
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [videoTitle, setVideoTitle] = useState('');

  useEffect(() => {
    if (!videoId) {
        setError("ID do vídeo não encontrado na URL.");
        setLoading(false);
        return;
    }
    if (!token) {
        setError("Autenticação necessária. Por favor, faça login.");
        setLoading(false); 
        return;
    }

    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      setGraphs(null); 
      setVideoTitle(''); 

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
          } else {
              try {
                  const errorData = await response.json();
                  errorMsg = errorData.detail || JSON.stringify(errorData);
              } catch(e) { /* Ignora erro ao fazer parse */ }
          }
          throw new Error(errorMsg);
        }

        const data = await response.json();
        
        if (!data || Object.values(data).every(value => value === null)) {
            setError("Nenhum gráfico pôde ser gerado para este vídeo. Verifique se o processamento foi concluído com sucesso.");
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

  }, [videoId, token, navigate]); 



  return (
    <Container className="mt-4">
      <Row className="mb-3 align-items-center">
        <Col xs="auto">

          <Link to="/video-list"> 
            <Button variant="outline-secondary" size="sm">&larr; Voltar</Button>
          </Link>
        </Col>
        <Col>
          <h2 className="mt-2 mb-0">Análises do Vídeo {videoTitle || `#${videoId}`}</h2>
        </Col>
      </Row>

      {loading && (
        <Row className="text-center mt-5">
          <Col>
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Carregando gráficos...</span>
            </Spinner>
            <p className="mt-2">A carregar gráficos...</p>
          </Col>
        </Row>
      )}

      {error && (
        <Row>
          <Col>
            <Alert variant="danger">Erro ao carregar gráficos: {error}</Alert>
          </Col>
        </Row>
      )}

      {graphs && !loading && !error && (
        <Row xs={1} md={2} className="g-4"> {/* Layout responsivo */}
          {Object.entries(graphs).map(([key, base64Image]) => (
            <Col key={key}>
              <Card className="h-100"> {/* h-100 para alinhar altura dos cards */}
                <Card.Header as="h5" className="text-capitalize">
                  {/* Melhora a formatação do título */}
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                </Card.Header>
                <Card.Body className="text-center d-flex align-items-center justify-content-center">
                  {base64Image ? ( 
                    <img 
                      src={base64Image} 
                      alt={`Gráfico ${key}`} 
                      className="img-fluid" // Torna a imagem responsiva
                      style={{ maxWidth: '100%', height: 'auto' }} // Garante bom ajuste
                    />
                  ) : (
                     <Alert variant="warning" className="mb-0">Gráfico não disponível.</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* Mensagem se não houver gráficos e não estiver carregando ou com erro */}
      {!graphs && !loading && !error && (
         <Row>
           <Col>
             <Alert variant="info">Nenhum gráfico disponível ou dados insuficientes para este vídeo.</Alert>
           </Col>
         </Row>
      )}

    </Container>
  );
}

export default VideoAnalyticsPage;