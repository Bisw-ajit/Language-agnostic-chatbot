import React, { useState, useContext } from 'react';
import { AuthContext } from '../App';
import client, { getErrorMessage } from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [role, setRole] = useState('student');
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (isRegistering) {
      try {
        await client.post('/auth/register', {
          email: email.trim(),
          password
        });
        setSuccessMsg('Account created successfully! You can now log in.');
        setIsRegistering(false);
      } catch (err) {
        setError(getErrorMessage(err, 'Registration failed. Please try again.'));
      }
      return;
    }

    try {
      const response = await client.post('/auth/login', {
        email: email.trim(),
        password
      });

      const token = response.data.access_token;
      const userRole = response.data.role || 'student';
      const userData = {
        id: response.data.user_id,
        email: response.data.email || email.trim(),
        role: userRole,
        tenant_id: response.data.tenant_id || 'default-tenant'
      };

      login(token, userRole, userData);
      if (userRole === 'admin' || userRole === 'super_admin') {
        navigate('/admin');
      } else {
        navigate('/chat');
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed. Please check your credentials.'));
    }
  };

  return (
    <div style={{ minHeight: '100dvh', background: 'var(--mist-paper, #f4f6f8)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ width: '100%', padding: 'clamp(14px, 3vw, 20px) clamp(16px, 4vw, 40px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontFamily: 'Fraunces, serif', fontSize: 'clamp(17px, 3.5vw, 20px)', color: 'var(--ink-indigo, #1e293b)', margin: 0 }}>
            Institutional Information Desk
          </h1>
          <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '12px', color: 'var(--slate-line, #64748b)', margin: '4px 0 0 0' }}>
            Ask anything. In your language.
          </p>
        </div>
      </header>
      
      <main style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 'clamp(16px, 4vw, 24px)' }}>
        <div style={{ background: 'white', width: '100%', maxWidth: '420px', padding: 'clamp(20px, 6vw, 36px)', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 16px rgba(0,0,0,0.06)' }}>
          <h2 style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600, fontSize: '20px', marginBottom: '20px', color: '#0f172a' }}>
            {isRegistering ? 'Create an account' : 'Sign in'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
                Email
              </label>
              <input 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. student@demo.com"
                style={{ width: '100%', padding: '12px', background: 'white', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }} 
                required 
              />
            </div>
            <div style={{ marginBottom: isRegistering ? '16px' : '24px' }}>
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
                Password
              </label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: '100%', padding: '12px', background: 'white', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }} 
                required 
              />
            </div>

            <button 
              type="submit"
              style={{ width: '100%', background: '#1e293b', color: 'white', fontFamily: 'Inter, sans-serif', fontWeight: 600, borderRadius: '6px', height: '44px', fontSize: '15px', border: 'none', cursor: 'pointer' }}
            >
              {isRegistering ? 'Register' : 'Login'}
            </button>

            {error && (
              <p style={{ color: '#ef4444', marginTop: '14px', fontSize: '13px', textAlign: 'center', lineHeight: 1.4 }}>{error}</p>
            )}
            {successMsg && (
              <p style={{ color: '#10b981', marginTop: '14px', fontSize: '13px', textAlign: 'center', lineHeight: 1.4 }}>{successMsg}</p>
            )}
          </form>

          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError(null);
                setSuccessMsg(null);
              }}
              style={{ background: 'none', border: 'none', fontSize: '13px', color: '#2563eb', cursor: 'pointer', textDecoration: 'underline', padding: '6px' }}
            >
              {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
