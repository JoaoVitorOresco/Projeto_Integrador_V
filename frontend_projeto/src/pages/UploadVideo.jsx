import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Form, Button, Container, Alert, Spinner, Row, Col } from 'react-bootstrap'; // Adicionado Spinner, Row, Col
import { FaCloudUploadAlt } from 'react-icons/fa';
import { ArrowLeftCircle, CheckCircle2, AlertCircle, Upload as UploadIcon } from 'lucide-react'; // Ícones
import { authContext } from '../context/AuthContext';
import styles from './UploadVideo.module.css'; 

function UploadVideo() {
  const [file, setFile] = useState(null);
  const [videoTitle, setVideoTitle] = useState(''); // Estado para o título do vídeo
  const [message, setMessage] = useState('');
  const [error, setError] = useState(''); // Estado separado para erros
  const [isLoading, setIsLoading] = useState(false);
  
  const { token } = useContext(authContext);
  const navigate = useNavigate();

  const handleFileChange = e => {
    const selected = e.target.files[0];
    if (selected) {
      // Validações básicas no frontend (opcional, mas bom para UX)
      const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/avi'];
      if (!allowedTypes.includes(selected.type)) {
        setError(`Formato de arquivo não suportado: ${selected.type}. Use MP4, MOV, AVI, MKV ou WEBM.`);
        setFile(null);
        return;
      }
      const maxSizeInBytes = 1024 * 1024 * 1024; // 1GB (ajuste conforme backend)
      if (selected.size > maxSizeInBytes) {
        setError(`Arquivo muito grande (${(selected.size / (1024*1024)).toFixed(2)}MB). Máximo: ${(maxSizeInBytes / (1024*1024))}MB.`);
        setFile(null);
        return;
      }
      setFile(selected);
      // Preenche o título com o nome do arquivo (sem extensão) se o título estiver vazio
      if (!videoTitle.trim()) {
        setVideoTitle(selected.name.split('.').slice(0, -1).join('.') || '');
      }
      setMessage(''); // Limpa mensagens anteriores
      setError('');   // Limpa erros anteriores
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!file) {
      setError('Por favor, selecione um vídeo.');
      return;
    }
    if (!videoTitle.trim()) { // Validação para o título
        setError('Por favor, insira um título para o vídeo.');
        return;
    }
    if (!token) {
        setError('Erro de autenticação. Por favor, faça login novamente.');
        navigate('/login'); // Redireciona se não houver token
        return;
    }

    const data = new FormData();
    data.append('video', file); 
    data.append('title', videoTitle); // Envia o título


    setIsLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch('/api/mmpose/videos/upload/', { 
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
          // 'Content-Type': 'multipart/form-data' é definido automaticamente pelo navegador
        },
        body: data 
      });

      const result = await response.json(); // Tenta parsear JSON mesmo se não for ok, para pegar erros do backend

      if (!response.ok) {
        // Usa a mensagem de erro do backend se disponível
        throw new Error(result.detail || result.error || result.message || `Erro no servidor: ${response.status}`);
      }
      
      setMessage(result.message || `Vídeo "${result.video?.title || videoTitle}" enviado com sucesso! Processamento iniciado.`);
      setFile(null); 
      setVideoTitle(''); // Limpa o campo de título
      // Limpa o input de arquivo visualmente
      if (document.getElementById('videoFile')) {
        document.getElementById('videoFile').value = "";
      }
      
    } catch (error) {
      console.error('Erro no upload:', error); 
      setError(`Falha no envio: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.pageWrapper}>
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

      <Container className={`py-5 ${styles.pageContainer}`}>
        <Row className="justify-content-center">
          <Col md={8} lg={7}> {/* Aumentei um pouco a largura do card */}
            <Card className={styles.formCard}>
              <Card.Body>
                <Card.Title className={`text-center mb-4 ${styles.formTitle}`}>
                  <FaCloudUploadAlt size={32} className="me-2" /> Enviar Vídeo para Análise
                </Card.Title>

                {message && (
                  <Alert variant='success' className={`mt-3 ${styles.alertBox}`} onClose={() => setMessage('')} dismissible>
                    <CheckCircle2 size={20} className="me-2"/> {message}
                  </Alert>
                )}
                {error && (
                  <Alert variant='danger' className={`mt-3 ${styles.alertBox}`} onClose={() => setError('')} dismissible>
                    <AlertCircle size={20} className="me-2"/> {error}
                  </Alert>
                )}

                <Form onSubmit={handleSubmit}>
                  <Form.Group controlId="videoTitle" className="mb-3">
                    <Form.Label className={styles.formLabel}>Título do Vídeo</Form.Label>
                    <Form.Control 
                      type="text" 
                      placeholder="Ex: Treino de Flechas - João vs Maria"
                      value={videoTitle}
                      onChange={(e) => setVideoTitle(e.target.value)}
                      required
                      disabled={isLoading}
                    />
                  </Form.Group>


                  <Form.Group controlId="videoFile" className="mb-4"> {/* Aumentei margin-bottom */}
                    <Form.Label className={styles.formLabel}>Selecione um vídeo</Form.Label>
                    <Form.Control 
                      type="file" 
                      accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm,video/avi" // Tipos aceitos
                      onChange={handleFileChange} 
                      disabled={isLoading}
                      required // Torna a seleção de arquivo obrigatória
                    />
                    {file && <small className="form-text text-muted mt-1 d-block">Selecionado: {file.name}</small>}
                  </Form.Group>
                  
                  <Button 
                    variant="primary" 
                    type="submit" 
                    className={`w-100 ${styles.actionButton}`} 
                    disabled={isLoading || !file || !videoTitle.trim()}
                  >
                    {isLoading ? (
                      <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" className="me-2"/>
                    ) : (
                      <UploadIcon size={18} className="me-2" />
                    )}
                    {isLoading ? 'Enviando...' : 'Enviar Vídeo'}
                  </Button>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default UploadVideo;