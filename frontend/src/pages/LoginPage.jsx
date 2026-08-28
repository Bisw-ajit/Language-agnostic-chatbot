import React, { useState, useContext } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await client.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const token = response.data.access_token;
      const role = response.data.role || 'student';

      login(token, role);
      if (role === 'admin' || role === 'super_admin') {
        navigate('/admin');
      } else {
        navigate('/chat');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--mist-paper)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ width: '100%', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontFamily: 'Fraunces', fontSize: '20px', color: 'var(--ink-indigo)', margin: 0 }}>
            Institutional Information Desk
          </h1>
          <p style={{ fontFamily: 'Inter', fontSize: '13px', color: 'var(--slate-line)', margin: '4px 0 0 0' }}>
            Ask anything. In your language.
          </p>
        </div>
        <div>
          <select style={{ padding: '8px', borderRadius: '4px', border: '1px solid var(--slate-line)', background: 'white' }}>
            <option>English</option>
            <option>हिन्दी</option>
            <option>ଓଡ଼ିଆ</option>
          </select>
        </div>
      </header>
      
      <main style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
        <div style={{ background: 'white', width: '100%', maxWidth: '420px', padding: '40px', border: '1px solid var(--slate-line)', borderRadius: '4px' }}>
          <h2 style={{ fontFamily: 'Inter', fontWeight: 600, fontSize: '22px', marginBottom: '24px' }}>Sign in</h2>
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Email
              </label>
              <input 
                type="text" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)}
                style={{ width: '100%', padding: '12px', background: 'white', border: '1px solid var(--slate-line)', borderRadius: '4px' }} 
                required 
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Password
              </label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ width: '100%', padding: '12px', background: 'white', border: '1px solid var(--slate-line)', borderRadius: '4px' }} 
                required 
              />
            </div>
            <button 
              type="submit"
              style={{ width: '100%', background: 'var(--ink-indigo)', color: 'white', fontFamily: 'Inter', fontWeight: 600, borderRadius: '4px', height: '44px', fontSize: '15px' }}
            >
              Login
            </button>
            {error && (
              <p style={{ color: 'var(--alert-rust)', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{error}</p>
            )}
          </form>
          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            <a href="#" style={{ fontSize: '14px', color: 'var(--ink-indigo)' }}>Don't have an account? Register</a>
          </div>
        </div>
      </main>
    </div>
  );
}
