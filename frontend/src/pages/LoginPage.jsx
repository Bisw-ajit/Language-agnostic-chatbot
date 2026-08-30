import React, { useState, useContext } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';
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
          password,
          role
        });
        setSuccessMsg('Account created successfully! You can now log in.');
        setIsRegistering(false);
      } catch (err) {
        setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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

      login(token, userRole);
      if (userRole === 'admin' || userRole === 'super_admin') {
        navigate('/admin');
      } else {
        navigate('/chat');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--mist-paper, #f4f6f8)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ width: '100%', padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontFamily: 'Fraunces, serif', fontSize: '20px', color: 'var(--ink-indigo, #1e293b)', margin: 0 }}>
            Institutional Information Desk
          </h1>
          <p style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px', color: 'var(--slate-line, #64748b)', margin: '4px 0 0 0' }}>
            Ask anything. In your language.
          </p>
        </div>
      </header>
      
      <main style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
        <div style={{ background: 'white', width: '100%', maxWidth: '420px', padding: '40px', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
          <h2 style={{ fontFamily: 'Inter, sans-serif', fontWeight: 600, fontSize: '22px', marginBottom: '24px', color: '#0f172a' }}>
            {isRegistering ? 'Create an account' : 'Sign in'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
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
              <label style={{ display: 'block', fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
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

            {isRegistering && (
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  style={{ width: '100%', padding: '12px', background: 'white', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                >
                  <option value="student">Student</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            )}

            <button 
              type="submit"
              style={{ width: '100%', background: '#1e293b', color: 'white', fontFamily: 'Inter, sans-serif', fontWeight: 600, borderRadius: '6px', height: '44px', fontSize: '15px', border: 'none', cursor: 'pointer' }}
            >
              {isRegistering ? 'Register' : 'Login'}
            </button>

            {error && (
              <p style={{ color: '#ef4444', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{error}</p>
            )}
            {successMsg && (
              <p style={{ color: '#10b981', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{successMsg}</p>
            )}
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError(null);
                setSuccessMsg(null);
              }}
              style={{ background: 'none', border: 'none', fontSize: '14px', color: '#2563eb', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
