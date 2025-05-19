import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Form, Button, Container, Alert } from 'react-bootstrap';
import { FaCloudUploadAlt } from 'react-icons/fa';
import { authContext } from '../context/AuthContext';

export default function UploadVideo() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { token } = useContext(authContext);
  const navigate = useNavigate();

  const handleChange = e => {
    setFile(e.target.files[0]);
    setMessage('');
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!file) {
      setMessage('Por favor, selecione um vídeo.');
      return;
    }
    if (!token) {
        setMessage('Erro de autenticação. Por favor, faça login novamente.');
        return;
    }

    const data = new FormData();
    data.append('video', file); 

    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/mmpose/videos/upload/', { 
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        },
        body: data 
      });

      if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch (jsonError) {
            errorData = { detail: response.statusText || `Erro no servidor: ${response.status}` };
        }
        throw new Error(errorData.detail || errorData.message || `Erro no servidor: ${response.status}`);
      }
      
      const result = await response.json();
      setMessage(result.message || 'Vídeo enviado com sucesso!');
      setFile(null); 
      
    } catch (error) {
      console.error('Erro no upload:', error); 
      setMessage(`Falha no envio: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container className="d-flex justify-content-center">
      <Card className="shadow upload-card" style={{width: '400px', marginTop: '50px'}}>
        <Card.Body>
          <Card.Title className="text-center mb-4">
            <FaCloudUploadAlt size={32} /> Enviar Vídeo
          </Card.Title>

          {message && (
            <Alert variant={message.includes('sucesso') ? 'success' : 'danger'} className="mt-3">
              {message}
            </Alert>
          )}

          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="videoFile" className="mb-3">
              <Form.Label>Selecione um vídeo</Form.Label>
              <Form.Control 
                type="file" 
                accept="video/*"
                onChange={handleChange} 
                disabled={isLoading}
              />
            </Form.Group>
            <Button 
              variant="primary" 
              type="submit" 
              className="w-100" 
              disabled={isLoading || !file}
            >
              {isLoading ? 'Enviando...' : 'Enviar'}
            </Button>
          </Form>
          <div className="text-center mt-3">
            <Button 
              as={Link} 
              to="/video-list" 
              variant="outline-secondary" 
              size="sm" 
              disabled={isLoading}
            >
              Voltar
            </Button>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}