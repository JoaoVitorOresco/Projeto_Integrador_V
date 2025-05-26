import React, { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Spinner, Alert, Button, ListGroup, Modal, Card } from 'react-bootstrap'; 
import { authContext } from '../context/AuthContext';
import { Upload, LogOut, PlayCircle, Download, Youtube, Trash2, Eye, AlertCircle, CheckCircle2 } from 'lucide-react'; 
import styles from './VideoListPage.module.css'; 

function VideoListPage() {
  const { token, logout } = useContext(authContext); 
  const navigate = useNavigate();
  
  const [videos, setVideos] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState(null); 

  const BACKEND_URL = 'http://localhost:8001'; 

  const fetchVideos = async (showLoadingIndicator = true) => {
    if (showLoadingIndicator) setLoading(true);
    setError(null);
    try {
      const apiUrl = '/api/mmpose/videos/'; 
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: { 'Authorization': `Token ${token}`, 'Content-Type': 'application/json' }
      });
      if (!response.ok) {
        let errorMsg = `Erro ${response.status}: ${response.statusText}`;
        if (response.status === 401 || response.status === 403) {
          errorMsg = "Sessão inválida ou expirada. Faça login novamente.";
          if (logout) logout(); navigate('/login');
        } else { try { const errorData = await response.json(); errorMsg = errorData.detail || JSON.stringify(errorData); } catch(e) {} }
        throw new Error(errorMsg);
      }
      const data = await response.json();
      const videosWithFullUrls = data.map(video => ({
        ...video,
        // A URL do vídeo local processado (se existir)
        processed_video_url_full: video.processed_video_file && !video.processed_video_file.startsWith('http') ? `${BACKEND_URL}${video.processed_video_file}` : video.processed_video_file,
        // A URL do vídeo original (se existir)
        original_video_url_full: video.video_file && !video.video_file.startsWith('http') ? `${BACKEND_URL}${video.video_file}` : video.video_file
      }));
      videosWithFullUrls.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      setVideos(videosWithFullUrls);
    } catch (err) {
      console.error("Erro ao buscar vídeos:", err);
      setError(err.message || "Falha ao carregar a lista de vídeos.");
    } finally {
      if (showLoadingIndicator) setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) { navigate('/login'); return; }
    fetchVideos();
  }, [token, navigate, logout]); 

  const handleLogout = () => { if (logout) logout(); navigate('/login'); };
  
  const formatDate = (dateString) => {
    if (!dateString) return 'Data indisponível';
    const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
  };
  
  const handleDownloadFromYouTube = async (videoId, videoTitle) => {
    if (!token) { setError("Autenticação necessária."); navigate('/login'); return; }
    setActionLoading(true); setError(null);
    const safeVideoTitle = videoTitle ? videoTitle.replace(/\s+/g, '_').replace(/[^\w-]/g, '') : 'video';
    const suggestedFilenameFallback = `${safeVideoTitle}_youtube.mp4`; 
    try {
      const backendDownloadUrl = `/api/mmpose/videos/download-from-youtube/?id=${videoId}`;
      const response = await fetch(backendDownloadUrl, { headers: { 'Authorization': `Token ${token}` } });
      if (!response.ok) { let errorMsg = `Falha: ${response.status}`; try { const ed = await response.json(); errorMsg = ed.error || ed.detail || errorMsg; } catch (e) {} throw new Error(errorMsg); }
      const blob = await response.blob(); const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.style.display = 'none'; a.href = url;
      const cd = response.headers.get('content-disposition'); let fn = suggestedFilenameFallback;
      if (cd) { const fm = cd.match(/filename="?(.+)"?/i); if (fm && fm.length === 2) fn = decodeURIComponent(fm[1].replace(/\+/g, ' ')); }
      a.download = fn; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); a.remove();
    } catch (err) { console.error('ERRO Download YouTube:', err); setError(err.message || 'Falha no download.');
    } finally { setActionLoading(false); }
  };

  const handleOpenDeleteConfirmModal = (video) => {
    setVideoToDelete(video); 
    setShowDeleteConfirmModal(true);
  };

  const handleCloseDeleteConfirmModal = () => {
    setShowDeleteConfirmModal(false);
    setVideoToDelete(null);
  };

  const handleConfirmDeleteVideo = async () => {
    if (!videoToDelete || !videoToDelete.youtube_video_id) {
      setError("Nenhum vídeo selecionado para deleção ou ID do YouTube faltando.");
      handleCloseDeleteConfirmModal(); return;
    }
    setActionLoading(true); setError(null);
    try {
      const deleteUrl = `/api/mmpose/videos/youtube/${videoToDelete.youtube_video_id}/delete/`;
      const response = await fetch(deleteUrl, { method: 'DELETE', headers: { 'Authorization': `Token ${token}` }});
      if (!response.ok) { let errorMsg = `Falha ao deletar: ${response.status}`; try { const ed = await response.json(); errorMsg = ed.error || ed.detail || errorMsg; } catch (e) {} throw new Error(errorMsg); }
      setVideos(prevVideos => prevVideos.map(v => v.id === videoToDelete.id ? { ...v, youtube_video_id: null, youtube_upload_status: 'deleted_from_youtube' } : v ));
    } catch (err) { console.error('ERRO ao deletar vídeo do YouTube:', err); setError(err.message || 'Falha ao deletar o vídeo do YouTube.');
    } finally { setActionLoading(false); handleCloseDeleteConfirmModal(); }
  };
  
  const getStatusVariant = (status) => {
    if (status === 'completed') return 'success';
    if (status === 'failed' || status === 'youtube_upload_failed') return 'danger';
    if (status === 'processing' || status === 'pending_youtube_upload') return 'warning';
    if (status === 'deleted_from_youtube') return 'secondary';
    return 'light';
  };
  
  if (loading && videos.length === 0 && !error && token) { 
    return (<Container className={`mt-5 text-center ${styles.pageContainer}`}><Spinner animation="border" variant="primary" /><p className="mt-3 text-primary">Carregando seus vídeos...</p></Container>);
  }
  if (error && !actionLoading) { 
    return (<Container className={`mt-5 ${styles.pageContainer}`}><Alert variant="danger" className={styles.alertBox}><AlertCircle size={20} className="me-2"/>{error}</Alert>{!token && <Button variant="primary" onClick={() => navigate('/login')}>Ir para Login</Button>}</Container>);
  }
  if (!token && !loading) { 
    return (<Container className={`mt-5 ${styles.pageContainer}`}><Alert variant="warning" className={styles.alertBox}>Autenticação necessária.</Alert><Button variant="primary" onClick={() => navigate('/login')}>Ir para Login</Button></Container>);
  }

  return (
    <div className={styles.pageWrapper}> {/* Usando a classe do CSS de referência */}
      <nav className={`navbar navbar-expand-lg ${styles.navbar}`}>
        <Container>
          <Link className={`navbar-brand ${styles.navbarBrand}`} to="/video-list">Esgrimetrics Análises</Link>
          <div className="d-flex">
            <Button variant="light" onClick={() => navigate('/upload')} className={`me-3 ${styles.navButton}`}>
              <Upload size={20} className="me-2" /> Enviar Vídeo
            </Button>
            <Button variant="outline-light" onClick={handleLogout} className={styles.navButton}>
              <LogOut size={20} className="me-2" /> Sair
            </Button>
          </div>
        </Container>
      </nav>

      <Container className={`py-4 ${styles.pageContainer}`}>
        <h2 className={`mb-4 ${styles.pageTitle}`}>Meus Vídeos</h2>
        
        {error && !actionLoading && videos.length > 0 && 
          <Alert variant="danger" onClose={() => setError(null)} dismissible className={styles.alertBox}>
            <AlertCircle size={20} className="me-2"/> {error}
          </Alert>
        }

        {videos.length === 0 && !loading && (
          <Card className={styles.card}>
            <Card.Body className="text-center">
              <Card.Title>Nenhum vídeo encontrado</Card.Title>
              <Card.Text>Você ainda não enviou nenhum vídeo para análise.</Card.Text>
              <Button variant="primary" onClick={() => navigate('/upload')} className={styles.actionButton}>
                <Upload size={18} className="me-1" /> Enviar seu primeiro vídeo
              </Button>
            </Card.Body>
          </Card>
        )}

        {videos.length > 0 && (
          <Row xs={1} md={2} lg={3} className="g-4">
            {videos.map(video => (
              <Col key={video.id}>
                <Card className={`${styles.videoCard} h-100`}>
                  <Card.Body className="d-flex flex-column">
                    <Card.Title className={styles.videoTitle}>{video.title || `Vídeo ${video.id}`}</Card.Title>
                    <Card.Text className={styles.videoInfo}><small>Enviado em: {formatDate(video.uploaded_at)}</small></Card.Text>
                    <Card.Text className={styles.videoInfo}>
                      <small>Estado Local: 
                        <span className={`ms-1 badge bg-${getStatusVariant(video.processing_status)}`}>
                          {video.processing_status || 'N/A'}
                        </span>
                      </small>
                    </Card.Text>
                    {video.youtube_video_id && video.youtube_upload_status !== 'deleted_from_youtube' && 
                      <Card.Text className={styles.videoInfo}><small>YouTube: <span className="ms-1 badge bg-success">Enviado</span></small></Card.Text>}
                    {video.youtube_upload_status === 'youtube_upload_failed' && 
                      <Card.Text className={styles.videoInfo}><small>YouTube: <span className="ms-1 badge bg-danger">Falha no envio</span></small></Card.Text>}
                    {video.youtube_upload_status === 'deleted_from_youtube' && 
                      <Card.Text className={styles.videoInfo}><small>YouTube: <span className="ms-1 badge bg-secondary">Deletado</span></small></Card.Text>}
                    
                    <div className={`mt-auto pt-3 d-flex flex-wrap gap-2 ${styles.actionsContainer}`}>
                      <Button 
                        variant="outline-primary" 
                        size="sm" 
                        onClick={() => navigate(`/videos/${video.id}/analytics`)}
                        disabled={video.processing_status !== 'completed'} 
                        title={video.processing_status !== 'completed' ? 'Processamento não concluído' : 'Ver Análise'}
                        className={styles.actionButton}
                      >
                        <Eye size={16} className="me-1" /> Análise
                      </Button>
                      
                      {video.youtube_video_id && video.youtube_upload_status !== 'deleted_from_youtube' && video.processing_status === 'completed' && (<>
                        <Button variant="outline-danger" size="sm" onClick={() => { const url = `https://www.youtube.com/watch?v=${video.youtube_video_id}`; window.open(url, '_blank');}} title="Assistir Vídeo no YouTube" className={styles.actionButton}>
                          <Youtube size={16} className="me-1" /> Assistir (YT)
                        </Button>
                        <Button variant="outline-success" size="sm" onClick={() => handleDownloadFromYouTube(video.id, video.title)} disabled={actionLoading} title="Baixar Vídeo do YouTube" className={styles.actionButton}>
                          <Download size={16} className="me-1" /> Baixar (YT)
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => handleOpenDeleteConfirmModal(video)} disabled={actionLoading} title="Deletar Vídeo do YouTube" className={styles.actionButton}>
                          <Trash2 size={16} />
                        </Button>
                      </>)}
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Container>

      <Modal show={showDeleteConfirmModal} onHide={handleCloseDeleteConfirmModal} centered>
        <Modal.Header closeButton className={styles.modalHeader}>
          <Modal.Title className={styles.modalTitle}>Confirmar Deleção</Modal.Title>
        </Modal.Header>
        <Modal.Body className={styles.modalBody}>
          Tem certeza que deseja deletar o vídeo "<strong>{videoToDelete?.title || 'este vídeo'}</strong>" do YouTube? Esta ação não pode ser desfeita no YouTube. O registro no seu sistema será atualizado.
        </Modal.Body>
        <Modal.Footer className={styles.modalFooter}>
          <Button variant="secondary" onClick={handleCloseDeleteConfirmModal} disabled={actionLoading} className={styles.buttonSecondary}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={handleConfirmDeleteVideo} disabled={actionLoading} className={styles.buttonDanger}>
            {actionLoading ? <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" className="me-1"/> : null}
            Deletar do YouTube
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default VideoListPage;