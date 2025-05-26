import React, { useState } from 'react';
import styles from './RegistrationPage.module.css';
import { Link, useNavigate  } from 'react-router-dom';
import axios from 'axios';
import sideImage from '../images/reg-side.jpeg';

function RegistrationPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password1, setPassword1] = useState(''); 
  const [password2, setPassword2] = useState(''); 
  const [errors, setErrors] = useState({}); 
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrors({}); 


    if (password1 !== password2) {
      setErrors({ password2: ['As senhas não coincidem.'] }); 
      return;
    }

    console.log('Enviando dados para cadastro:', { username, email, password1});

 
    try {
      const payload = {
        username: username,
        email: email,
        password1: password1,
        password2: password2,
      };
      
      console.log('Enviando payload:', payload);
      const response = await axios.post('/api/auth/registration/', payload, {
        headers: { 'Content-Type': 'application/json' },
      });

      console.log('Usuário cadastrado:', response.data);
      alert('Cadastro realizado com sucesso! Você será redirecionado para o login.');
      navigate('/login');

    } catch (err) {
      console.error('Erro no cadastro DETALHADO:', err.response ? err.response.data : err);
      if (err.response && err.response.data) {
        setErrors(err.response.data);
      } else if (err.request) {
         setErrors({ general: ['Não foi possível conectar ao servidor. Verifique sua conexão.'] });
      } else {
         setErrors({ general: ['Ocorreu um erro inesperado durante o cadastro.'] });
      }
    }
    // -------------------------------------------------------------------
  };

  return (

    <div className={styles.pageWrapper}>
      <div className={styles.left}>
        <h1 className={styles.formTitle || 'text-center mb-4'}>Cadastro de Usuário</h1>

        {errors.non_field_errors && ( <div className="alert alert-danger">{errors.non_field_errors.join(' ')}</div> )}
        {errors.detail && ( <div className="alert alert-danger">{errors.detail}</div> )}
         {errors.general && ( <div className="alert alert-danger">{errors.general.join(' ')}</div> )}


        <form onSubmit={handleSubmit}>
           <div className="mb-3 text-start">
            <label htmlFor="username" className="form-label">Nome de Usuário</label>
            <input
              type="text" id="username" name="username" className="form-control"
              placeholder="Escolha um nome de usuário" required
              value={username} onChange={(e) => setUsername(e.target.value)}
            />
            {errors.username && <div className="text-danger mt-1" style={{fontSize: '0.875em'}}>{errors.username.join(', ')}</div>}
          </div>

          <div className="mb-3 text-start">
            <label htmlFor="emailReg" className="form-label">E-mail</label>
            <input
              type="email" id="emailReg" name="email" className="form-control"
              placeholder="Digite seu e-mail" required
              value={email} onChange={(e) => setEmail(e.target.value)}
            />
            {errors.email && <div className="text-danger mt-1" style={{fontSize: '0.875em'}}>{errors.email.join(', ')}</div>}
          </div>

          <div className="mb-3 text-start">
            <label htmlFor="passwordReg" className="form-label">Senha</label>
            <input
              type="password" id="passwordReg" name="password1" className="form-control"
              placeholder="Digite sua senha" required
              value={password1} onChange={(e) => setPassword1(e.target.value)}
            />
             {errors.password1 && <div className="text-danger mt-1" style={{fontSize: '0.875em'}}>{errors.password1.join(', ')}</div>}
          </div>

          <div className="mb-3 text-start">
            <label htmlFor="password2" className="form-label">Confirmar Senha</label>
            <input
              type="password" id="password2" name="password2" className="form-control"
              placeholder="Digite sua senha novamente" required
              value={password2} onChange={(e) => setPassword2(e.target.value)}
            />
             {errors.password2 && <div className="text-danger mt-1" style={{fontSize: '0.875em'}}>{errors.password2.join(', ')}</div>}
          </div>

          <div className="text-center">
            <button type="submit" className="btn btn-primary btn-lg w-100">Cadastrar</button>
          </div>
        </form>

        <div className="text-center mt-3">
          <Link to="/login" className="text-decoration-none">Já tem uma conta? Entre</Link>
        </div>
      </div>
      <div
        className={styles.right}
        style={{
          flex: '0 0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem'
        }}
      >
        <img
          src={sideImage}
          alt="Registration illustration"
          style={{ width: '1280px', height: '720px', objectFit: 'cover', borderRadius: '16px' }}
        />
      </div>
    </div>
  );
}

export default RegistrationPage;