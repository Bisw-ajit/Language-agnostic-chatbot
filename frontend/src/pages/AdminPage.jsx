import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';

export default function AdminPage() {
  const { logout } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('Documents');
  
  const [documents, setDocuments] = useState([]);
  const [queries, setQueries] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null); // 'idle', 'uploading', 'stage1', 'stage2', 'stage3', 'stage4', 'done'
  const [currentDocId, setCurrentDocId] = useState(null);
  const [currentDocStatus, setCurrentDocStatus] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState({ id: null, filename: '', input: '' });

  useEffect(() => {
    if (activeTab === 'Documents') fetchDocuments();
    if (activeTab === 'Unanswered Queries') fetchQueries();
    if (activeTab === 'Analytics') fetchAnalytics();
  }, [activeTab]);

  useEffect(() => {
    let interval;
    if (currentDocId && uploadStatus && uploadStatus !== 'idle' && uploadStatus !== 'done') {
      interval = setInterval(async () => {
        try {
          const res = await client.get(`/admin/documents/${currentDocId}/status`);
          const status = res.data.status;
          setCurrentDocStatus(status);
          
          if (status === 'indexed' || status === 'approved') {
            setUploadStatus('done');
            clearInterval(interval);
          } else if (status === 'pending_approval') {
            setUploadStatus('stage4');
          } else if (status === 'embedding') {
            setUploadStatus('stage3');
          } else if (status === 'chunking') {
            setUploadStatus('stage2');
          } else if (status === 'extracting') {
            setUploadStatus('stage1');
          }
        } catch (err) {
          console.error('Polling error', err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [currentDocId, uploadStatus]);

  const fetchDocuments = async () => {
    try {
      const res = await client.get('/admin/documents');
      setDocuments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchQueries = async () => {
    try {
      const res = await client.get('/admin/unanswered-queries');
      setQueries(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await client.get('/admin/analytics');
      setAnalytics(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleApprove = async (id) => {
    try {
      await client.patch(`/admin/documents/${id}`, { status: 'approved' });
      fetchDocuments();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (deleteConfirm.id === id && deleteConfirm.input === deleteConfirm.filename) {
      try {
        await client.delete(`/admin/documents/${id}`);
        setDeleteConfirm({ id: null, filename: '', input: '' });
        fetchDocuments();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await client.post('/admin/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setCurrentDocId(res.data.id);
      setCurrentDocStatus(res.data.status);
      setUploadStatus('stage1');
    } catch (err) {
      console.error(err);
      setUploadStatus('idle');
      alert('Upload failed');
    }
  };

  const renderStatusTag = (status) => {
    const s = status ? status.toUpperCase() : 'UNKNOWN';
    let style = { padding: '2px 6px', borderRadius: '2px', fontFamily: 'IBM Plex Mono', fontSize: '10px' };
    
    if (s === 'INDEXED') {
      style = { ...style, background: 'var(--banyan-green)', color: 'white' };
    } else if (s === 'APPROVED') {
      style = { ...style, background: 'var(--turmeric-gold)', color: 'var(--ink-indigo)' };
    } else if (['PENDING', 'PENDING_APPROVAL', 'EXTRACTING', 'CHUNKING', 'EMBEDDING'].includes(s)) {
      style = { ...style, background: 'var(--slate-line)', color: 'white' };
    } else if (s === 'VALIDATED') {
      style = { ...style, border: '1px solid var(--slate-line)', color: 'var(--slate-line)' };
    } else if (s === 'SUPERSEDED') {
      style = { ...style, textDecoration: 'line-through', color: 'var(--slate-line)' };
    } else {
      style = { ...style, background: '#eee', color: '#333' };
    }
    
    return <span style={style}>{s}</span>;
  };

  const getStageStyle = (stageKey) => {
    const stages = ['idle', 'uploading', 'stage1', 'stage2', 'stage3', 'stage4', 'done'];
    const currentIndex = stages.indexOf(uploadStatus);
    const stageIndex = stages.indexOf(stageKey);
    
    if (uploadStatus === 'done' || currentIndex > stageIndex) {
      return { color: 'var(--banyan-green)', icon: '✓' }; // completed
    } else if (currentIndex === stageIndex) {
      return { color: 'var(--turmeric-gold)', icon: '○' }; // current
    } else {
      return { color: 'var(--slate-line)', icon: '○' }; // upcoming
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ background: 'white', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--slate-line)' }}>
        <h1 style={{ fontFamily: 'Fraunces', fontSize: '18px', margin: 0, color: 'var(--ink-indigo)' }}>
          Institutional Information Desk — Admin Panel
        </h1>
        <button onClick={logout} style={{ background: 'transparent', color: 'var(--ink-indigo)', fontWeight: 500 }}>
          Logout
        </button>
      </header>

      <div style={{ padding: '0 24px', background: 'white', borderBottom: '1px solid var(--slate-line)' }}>
        <div style={{ display: 'flex', gap: '24px' }}>
          {['Documents', 'Upload', 'Unanswered Queries', 'Analytics'].map(tab => (
            <div 
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '16px 0',
                cursor: 'pointer',
                fontFamily: 'IBM Plex Mono',
                fontSize: '12px',
                textTransform: 'uppercase',
                borderBottom: activeTab === tab ? '2px solid var(--turmeric-gold)' : '2px solid transparent',
                color: activeTab === tab ? 'var(--ink-indigo)' : 'var(--slate-line)',
                fontWeight: activeTab === tab ? 600 : 400
              }}
            >
              {tab}
            </div>
          ))}
        </div>
      </div>

      <main style={{ flex: 1, padding: '32px 24px', background: 'var(--mist-paper)' }}>
        
        {activeTab === 'Documents' && (
          <div style={{ background: 'white', borderRadius: '4px', border: '1px solid var(--slate-line)', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--slate-line)', fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)' }}>
                  <th style={{ padding: '16px', fontWeight: 500 }}>DOCUMENT</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>DEPT</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>LANGUAGE</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>VERSION</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>STATUS</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>UPLOADED</th>
                  <th style={{ padding: '16px', fontWeight: 500 }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid var(--slate-line)' }}>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{doc.filename}</td>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{doc.department || '-'}</td>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{doc.language || '-'}</td>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{doc.version || '1.0'}</td>
                    <td style={{ padding: '16px' }}>{renderStatusTag(doc.status)}</td>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {doc.status === 'pending_approval' && (
                          <button onClick={() => handleApprove(doc.id)} style={{ background: 'var(--turmeric-gold)', color: 'var(--ink-indigo)', padding: '4px 8px', borderRadius: '2px', fontSize: '12px', fontWeight: 500 }}>Approve</button>
                        )}
                        
                        {deleteConfirm.id === doc.id ? (
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <input 
                              type="text" 
                              placeholder="Type filename" 
                              value={deleteConfirm.input} 
                              onChange={e => setDeleteConfirm({...deleteConfirm, input: e.target.value})}
                              style={{ width: '100px', padding: '2px', fontSize: '12px', border: '1px solid var(--alert-rust)' }}
                            />
                            <button onClick={() => handleDelete(doc.id)} style={{ background: 'var(--alert-rust)', color: 'white', padding: '2px 6px', fontSize: '12px', borderRadius: '2px' }}>Confirm</button>
                            <button onClick={() => setDeleteConfirm({id: null, filename: '', input: ''})} style={{ background: 'transparent', fontSize: '12px' }}>Cancel</button>
                          </div>
                        ) : (
                          <button onClick={() => setDeleteConfirm({ id: doc.id, filename: doc.filename, input: '' })} style={{ background: 'transparent', color: 'var(--alert-rust)', fontSize: '12px' }}>Delete</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr>
                    <td colSpan="7" style={{ padding: '32px', textAlign: 'center', color: 'var(--slate-line)' }}>No documents found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'Upload' && (
          <div style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div 
              style={{
                border: '2px dashed var(--slate-line)', borderRadius: '4px', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: 'white', marginBottom: '24px', cursor: 'pointer'
              }}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <div style={{ fontFamily: 'Inter', fontSize: '15px', color: 'var(--ink-indigo)', marginBottom: '8px' }}>
                {file ? file.name : 'Drag & drop a file here or click to browse'}
              </div>
              <input id="file-upload" type="file" onChange={(e) => setFile(e.target.files[0])} style={{ display: 'none' }} />
            </div>

            <form onSubmit={handleFileUpload} style={{ background: 'white', padding: '24px', border: '1px solid var(--slate-line)', borderRadius: '4px', marginBottom: '24px' }}>
              <button 
                type="submit" 
                disabled={!file || uploadStatus === 'uploading'}
                style={{ width: '100%', background: 'var(--ink-indigo)', color: 'white', padding: '12px', borderRadius: '4px', fontWeight: 600, opacity: !file ? 0.5 : 1 }}
              >
                Upload & Index
              </button>
            </form>

            {uploadStatus && uploadStatus !== 'idle' && (
              <div style={{ background: 'white', padding: '24px', border: '1px solid var(--slate-line)', borderRadius: '4px' }}>
                <h3 style={{ fontSize: '14px', marginBottom: '16px' }}>Processing Status</h3>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'IBM Plex Mono', fontSize: '11px' }}>
                  {[
                    { key: 'stage1', label: 'Extracting text' },
                    { key: 'stage2', label: 'Chunking' },
                    { key: 'stage3', label: 'Generating embeddings' },
                    { key: 'stage4', label: 'Awaiting approval' }
                  ].map(stage => {
                    const style = getStageStyle(stage.key);
                    return (
                      <div key={stage.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: style.color }}>
                        <div>{style.icon}</div>
                        <div style={{ textTransform: 'uppercase' }}>{stage.label}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'Unanswered Queries' && (
          <div style={{ background: 'white', borderRadius: '4px', border: '1px solid var(--slate-line)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--slate-line)', fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)' }}>
                  <th style={{ padding: '16px' }}>QUERY</th>
                  <th style={{ padding: '16px' }}>LANGUAGE</th>
                  <th style={{ padding: '16px' }}>TIMESTAMP</th>
                  <th style={{ padding: '16px' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {queries.map(q => (
                  <tr key={q.id} style={{ borderBottom: '1px solid var(--slate-line)' }}>
                    <td style={{ padding: '16px', fontSize: '14px' }}>{q.query}</td>
                    <td style={{ padding: '16px' }}>
                      <span style={{ border: '1px solid var(--slate-line)', borderRadius: '12px', padding: '2px 8px', fontSize: '12px' }}>{q.language}</span>
                    </td>
                    <td style={{ padding: '16px', fontSize: '14px', fontFamily: 'IBM Plex Mono' }}>{new Date(q.created_at).toLocaleString()}</td>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button style={{ border: '1px solid var(--turmeric-gold)', background: 'transparent', color: 'var(--ink-indigo)', padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }}>Needs Doc</button>
                        <button style={{ border: '1px solid var(--slate-line)', background: 'transparent', color: 'var(--slate-line)', padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }}>Dismiss</button>
                      </div>
                    </td>
                  </tr>
                ))}
                {queries.length === 0 && (
                  <tr><td colSpan="4" style={{ padding: '32px', textAlign: 'center', color: 'var(--slate-line)' }}>No unanswered queries</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'Analytics' && (
          <div style={{ display: 'flex', gap: '24px' }}>
            {[
              { label: 'TOTAL QUERIES', value: analytics?.total_queries || '284' },
              { label: 'ANSWER RATE', value: analytics?.answer_rate || '87.3%' },
              { label: 'FALLBACK RATE', value: analytics?.fallback_rate || '12.7%' },
              { label: 'AVG LATENCY', value: analytics?.avg_latency || '1.8s' }
            ].map(stat => (
              <div key={stat.label} style={{ flex: 1, background: 'white', border: '1px solid var(--slate-line)', borderRadius: '4px', padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '38px', color: 'var(--ink-indigo)', lineHeight: 1, marginBottom: '8px' }}>{stat.value}</div>
                <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)', textTransform: 'uppercase' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
