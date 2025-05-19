import React from 'react';
import { Button, Container } from 'react-bootstrap';
import styles from './HomePage.module.css';
import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className={styles.homePageComFundo}>
      <div className={styles.overlay}>
        <Container className="text-center text-white">
          <h1 className="display-4 mb-3">Esgrimetrics</h1>
          <p className="lead mb-4">
            Nosso sistema faz análise de dados de lutas de esgrima, extraindo estatísticas de movimento, postura e desempenho dos atletas.
          </p>
          <div className="d-flex justify-content-center">
            <Button as={Link} to="/login" variant="light" size="lg" className="me-3">
              Login
            </Button>
            <Button as={Link} to="/cadastro" variant="outline-light" size="lg">
              Cadastrar-se
            </Button>
          </div>
        </Container>
      </div>
    </div>
  );
}

