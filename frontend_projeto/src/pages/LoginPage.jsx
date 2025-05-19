import React, { useState, useContext} from 'react';
import styles from './LoginPage.module.css';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { authContext } from '../context/AuthContext';


function LoginPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();
  const { login } = useContext(authContext);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    console.log('Tentando fazer login com:', { username, email, password });

    try {
      const response = await axios.post('/api/auth/login/', {
        username: username,
        email: email,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
      });

      console.log('Login API bem-sucedido:', response.data);
      const token = response.data.key; 
      const userDataFromApi = null; 

      await login(token, userDataFromApi); 

      navigate('/video-list'); 

    } catch (err) {
      console.error('Erro no login:', err);
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        let errorMessage = "Erro desconhecido.";
        if (errorData.non_field_errors) {
          errorMessage = errorData.non_field_errors.join(' ');
        } else if (typeof errorData === 'object') {
          errorMessage = Object.entries(errorData)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
        setError(errorMessage);
      } else if (err.request) {
        setError('Não foi possível conectar ao servidor. Verifique sua conexão.');
      } else {
        setError('Ocorreu um erro inesperado durante o login.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <nav className="navbar navbar-light bg-light">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">Login de Usuários</Link>
        </div>
      </nav>

      <div className="container d-flex justify-content-center align-items-center" style={{ minHeight: 'calc(100vh - 56px)' }}>
        <div className="col-md-6">
          <h1 className="text-center mb-4">Login</h1>

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>

              <div className="mb-3">
              <label htmlFor="usernameInput" className="form-label">Nome de Usuário</label>
              <input
                id="usernameInput"
                name="username"
                className="form-control"
                type="text"
                placeholder="Digite seu nome de usuário"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            
            <div className="mb-3">
              <label htmlFor="emailInput" className="form-label">E-mail</label>
              <input
                id="emailInput"
                name="email"
                className="form-control"
                type="email"
                placeholder="Digite seu e-mail"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            
            <div className="mb-3">
              <label htmlFor="passwordInput" className="form-label">Senha</label>
              <input
                id="passwordInput"
                name="password"
                className="form-control"
                type="password"
                placeholder="Digite sua senha"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="text-center">
              <button type="submit" className="btn btn-primary btn-lg w-100">Entrar</button>
            </div>
          </form>

          <div className="text-center mt-3">
            <Link to="/cadastro" className="text-decoration-none">Não tem uma conta? Cadastre-se</Link>
          </div>
        </div>
      </div>
    </>
  );
}

export default LoginPage;