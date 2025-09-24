import { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://127.0.0.1:5000';

const LoginPage = ({ onLoginSuccess }) => {
  const [passkey, setPasskey] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/api/login`, { passkey });
      if (response.data.success) {
        onLoginSuccess();
      }
    } catch (err) {
      setError('Invalid passkey. Please try again.');
    }
  };

  return (
    <div className="login-box">
      <h1>Welcome</h1>
      <p>Please enter the passkey to continue.</p>
      <form onSubmit={handleLogin}>
        <input
          type="password"
          placeholder="Passkey"
          value={passkey}
          onChange={(e) => setPasskey(e.target.value)}
        />
        <button type="submit">Login</button>
      </form>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default LoginPage;