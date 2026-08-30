import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';

export default function AdminPage() {
  const { logout } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('Documents');
  
  const [documents, setDocuments] = useState([]);
  const [queries, setQueries] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Upload form state
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Agriculture & Farmers Empowerment');
  const [docLanguage, setDocLanguage] = useState('en');
  const [version, setVersion] = useState('2024.1');
  const [category, setCategory] = useState('Scheme');
  const [sourceType, setSourceType] = useState('official');
  const [authorityLevel, setAuthorityLevel] = useState('official');
  const [sourceUrl, setSourceUrl] = useState('');
  
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle', 'uploading', 'stage1', 'stage2', 'stage3', 'stage4', 'done'
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
          
          if (status === 'active' || status === 'indexed' || status === 'approved') {
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
      console.error('Failed to fetch documents', err);
    }
  };

  const fetchQueries = async () => {
    try {
      const res = await client.get('/admin/unanswered-queries');
      setQueries(res.data);
    } catch (err) {
      console.error('Failed to fetch queries', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await client.get('/admin/analytics');
      setAnalytics(res.data);
    } catch (err) {
      console.error('Failed to fetch analytics', err);
    }
  };

  const handleApprove = async (id) => {
    try {
      await client.patch(`/admin/documents/${id}`, { status: 'approved' });
      fetchDocuments();
    } catch (err) {
      console.error(err);
      alert('Approval failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleArchive = async (id) => {
    try {
      await client.patch(`/admin/documents/${id}`, { status: 'archived' });
      fetchDocuments();
    } catch (err) {
      console.error(err);
      alert('Archive failed: ' + (err.response?.data?.detail || err.message));
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
        alert('Delete failed: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || file.name.replace('.pdf', ''));
    formData.append('department', department);
    formData.append('category', category);
    formData.append('language', docLanguage);
    formData.append('version', version);
    formData.append('source_type', sourceType);
    formData.append('authority_level', authorityLevel);
    if (sourceUrl) formData.append('source_url', sourceUrl);
    
    try {
      const res = await client.post('/admin/documents', formData);
      setCurrentDocId(res.data.id);
      setCurrentDocStatus('pending');
      setUploadStatus('stage1');
      fetchDocuments();
    } catch (err) {
      console.error(err);
      setUploadStatus('idle');
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const renderStatusTag = (status) => {
    const s = status ? status.toUpperCase() : 'UNKNOWN';
    let style = { padding: '3px 8px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '10px', fontWeight: 600, display: 'inline-block' };
    
    if (s === 'ACTIVE' || s === 'INDEXED') {
      return <span style={{ ...style, background: '#dcfce7', color: '#15803d' }}>ACTIVE</span>;
    } else if (s === 'PENDING_APPROVAL' || s === 'APPROVED') {
      return <span style={{ ...style, background: '#fef3c7', color: '#b45309' }}>PENDING APPROVAL</span>;
    } else if (s === 'ARCHIVED' || s === 'SUPERSEDED') {
      return <span style={{ ...style, background: '#f1f5f9', color: '#64748b' }}>ARCHIVED</span>;
    } else if (['EXTRACTING', 'CHUNKING', 'EMBEDDING'].includes(s)) {
      return <span style={{ ...style, background: '#e0f2fe', color: '#0369a1' }}>{s}...</span>;
    } else if (s === 'FAILED' || s === 'REJECTED') {
      return <span style={{ ...style, background: '#fee2e2', color: '#b91c1c' }}>FAILED</span>;
    } else {
      return <span style={{ ...style, background: '#f1f5f9', color: '#475569' }}>{s}</span>;
    }
  };

  const getStageStyle = (stageKey) => {
    const stages = ['idle', 'uploading', 'stage1', 'stage2', 'stage3', 'stage4', 'done'];
    const currentIndex = stages.indexOf(uploadStatus);
    const stageIndex = stages.indexOf(stageKey);
    
    if (uploadStatus === 'done' || currentIndex > stageIndex) {
      return { color: '#15803d', icon: '✓' }; // completed
    } else if (currentIndex === stageIndex) {
      return { color: '#2563eb', icon: '○' }; // current
    } else {
      return { color: '#94a3b8', icon: '○' }; // upcoming
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      <header style={{ background: 'white', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <a href="/chat" style={{ fontSize: '13px', color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>
            ← Back to Chat
          </a>
          <h1 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#0f172a' }}>
            Institutional Knowledge Administration
          </h1>
        </div>
        <button 
          onClick={logout} 
          style={{ background: '#f1f5f9', color: '#475569', border: 'none', padding: '6px 14px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
        >
          Logout
        </button>
      </header>

      <div style={{ padding: '0 24px', background: 'white', borderBottom: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', gap: '24px' }}>
          {['Documents', 'Upload', 'Unanswered Queries', 'Analytics'].map(tab => (
            <div 
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '14px 0',
                cursor: 'pointer',
                fontSize: '13px',
                borderBottom: activeTab === tab ? '2px solid #2563eb' : '2px solid transparent',
                color: activeTab === tab ? '#2563eb' : '#64748b',
                fontWeight: activeTab === tab ? 700 : 500
              }}
            >
              {tab}
            </div>
          ))}
        </div>
      </div>

      <main style={{ flex: 1, padding: '24px', maxWidth: '1200px', width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
        
        {activeTab === 'Documents' && (
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Managed Documents ({documents.length})
              </div>
              <button
                onClick={() => setActiveTab('Upload')}
                style={{ background: '#2563eb', color: 'white', border: 'none', padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
              >
                + Upload New Document
              </button>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Title / Filename</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Department</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Authority</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Ver</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Checksum</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>{doc.title || doc.filename}</div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>{doc.filename}</div>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#475569' }}>{doc.department || '-'}</td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ 
                        fontSize: '10px', 
                        padding: '2px 6px', 
                        borderRadius: '3px', 
                        fontWeight: 700, 
                        textTransform: 'uppercase',
                        background: doc.authority_level === 'official' ? '#dcfce7' : doc.authority_level === 'demo' ? '#f3e8ff' : '#e0f2fe',
                        color: doc.authority_level === 'official' ? '#15803d' : doc.authority_level === 'demo' ? '#7e22ce' : '#0369a1'
                      }}>
                        {doc.authority_level || 'OFFICIAL'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', fontFamily: 'monospace', color: '#475569' }}>v{doc.version || '1.0'}</td>
                    <td style={{ padding: '14px 16px' }}>{renderStatusTag(doc.status)}</td>
                    <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontSize: '11px', color: '#94a3b8' }}>
                      {doc.checksum ? `${doc.checksum.substring(0, 8)}...` : '-'}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {doc.status === 'pending_approval' && (
                          <button 
                            onClick={() => handleApprove(doc.id)} 
                            style={{ background: '#22c55e', color: 'white', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, cursor: 'pointer' }}
                          >
                            Approve
                          </button>
                        )}
                        {doc.status === 'active' && (
                          <button 
                            onClick={() => handleArchive(doc.id)} 
                            style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 500, cursor: 'pointer' }}
                          >
                            Archive
                          </button>
                        )}
                        
                        {deleteConfirm.id === doc.id ? (
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <input 
                              type="text" 
                              placeholder="Type filename" 
                              value={deleteConfirm.input} 
                              onChange={e => setDeleteConfirm({...deleteConfirm, input: e.target.value})}
                              style={{ width: '110px', padding: '3px', fontSize: '11px', border: '1px solid #ef4444', borderRadius: '3px' }}
                            />
                            <button onClick={() => handleDelete(doc.id)} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '3px 8px', fontSize: '11px', borderRadius: '3px', cursor: 'pointer' }}>Confirm</button>
                            <button onClick={() => setDeleteConfirm({id: null, filename: '', input: ''})} style={{ background: 'transparent', border: 'none', fontSize: '11px', cursor: 'pointer', color: '#64748b' }}>Cancel</button>
                          </div>
                        ) : (
                          <button 
                            onClick={() => setDeleteConfirm({ id: doc.id, filename: doc.filename, input: '' })} 
                            style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: '11px', cursor: 'pointer', fontWeight: 500 }}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr>
                    <td colSpan="7" style={{ padding: '32px', textAlign: 'center', color: '#94a3b8' }}>No documents registered.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'Upload' && (
          <div style={{ maxWidth: '680px', margin: '0 auto' }}>
            <div 
              style={{
                border: '2px dashed #cbd5e1', borderRadius: '8px', padding: '32px 16px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: 'white', marginBottom: '20px', cursor: 'pointer'
              }}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>📄</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '4px' }}>
                {file ? file.name : 'Choose a PDF document or drag and drop here'}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                Upload official scheme guidelines, institutional circulars, or policy documents
              </div>
              <input id="file-upload" type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} style={{ display: 'none' }} />
            </div>

            <form onSubmit={handleFileUpload} style={{ background: 'white', padding: '24px', border: '1px solid #e2e8f0', borderRadius: '8px', marginBottom: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                  Document Title / Scheme Name
                </label>
                <input 
                  type="text" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. KALIA Yojana Guidelines"
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '14px', marginBottom: '14px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Department
                  </label>
                  <input 
                    type="text" 
                    value={department} 
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. Agriculture & Farmers Empowerment"
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                    required
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Version
                  </label>
                  <input 
                    type="text" 
                    value={version} 
                    onChange={(e) => setVersion(e.target.value)}
                    placeholder="e.g. 2024.1"
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '14px', marginBottom: '14px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Authority Level
                  </label>
                  <select
                    value={authorityLevel}
                    onChange={(e) => setAuthorityLevel(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box', background: 'white' }}
                  >
                    <option value="official">Official (Government / Institutional)</option>
                    <option value="trusted">Trusted (Verified Partner)</option>
                    <option value="demo">Demo (Demo Knowledge Base)</option>
                    <option value="user_uploaded">User Uploaded</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Language
                  </label>
                  <select
                    value={docLanguage}
                    onChange={(e) => setDocLanguage(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box', background: 'white' }}
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="or">Odia</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                  Official Source URL (Optional)
                </label>
                <input 
                  type="url" 
                  value={sourceUrl} 
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://kalia.odisha.gov.in"
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <button 
                type="submit" 
                disabled={!file || uploadStatus === 'uploading'}
                style={{ width: '100%', background: '#2563eb', color: 'white', padding: '12px', borderRadius: '6px', fontWeight: 600, fontSize: '14px', border: 'none', opacity: !file ? 0.5 : 1, cursor: !file ? 'not-allowed' : 'pointer' }}
              >
                Upload & Ingest Document
              </button>
            </form>

            {uploadStatus && uploadStatus !== 'idle' && (
              <div style={{ background: 'white', padding: '20px', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '14px' }}>Processing Pipeline Status</h3>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontFamily: 'monospace' }}>
                  {[
                    { key: 'stage1', label: 'Extracting text' },
                    { key: 'stage2', label: 'Chunking' },
                    { key: 'stage3', label: 'Generating embeddings' },
                    { key: 'stage4', label: 'Awaiting approval' }
                  ].map(stage => {
                    const style = getStageStyle(stage.key);
                    return (
                      <div key={stage.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', color: style.color }}>
                        <div style={{ fontSize: '14px', fontWeight: 700 }}>{style.icon}</div>
                        <div style={{ textTransform: 'uppercase' }}>{style.label}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'Unanswered Queries' && (
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
              Queries Triggering Fallback / Unanswered ({queries.length})
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>User Query</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600 }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {queries.map((q) => (
                  <tr key={q.id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '13px' }}>
                    <td style={{ padding: '14px 16px', color: '#0f172a' }}>{q.user_query}</td>
                    <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '12px' }}>{new Date(q.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
                {queries.length === 0 && (
                  <tr>
                    <td colSpan={2} style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                      No unanswered queries yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
