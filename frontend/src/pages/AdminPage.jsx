import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../App';
import client, { getErrorMessage } from '../api/client';

export default function AdminPage() {
  const { logout, user } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('Documents');
  
  const [documents, setDocuments] = useState([]);
  const [queries, setQueries] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
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
  
  const [uploadStatus, setUploadStatus] = useState('idle');
  const [currentDocId, setCurrentDocId] = useState(null);
  const [currentDocStatus, setCurrentDocStatus] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState({ id: null, filename: '', input: '' });

  useEffect(() => {
    if (activeTab === 'Documents') fetchDocuments();
    if (activeTab === 'Unanswered Queries') fetchQueries();
    if (activeTab === 'Audit Logs') fetchAuditLogs();
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

  const fetchAuditLogs = async () => {
    try {
      const res = await client.get('/admin/audit-logs');
      setAuditLogs(res.data.logs || []);
    } catch (err) {
      console.error('Failed to fetch audit logs', err);
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
      alert('Approval failed: ' + getErrorMessage(err));
    }
  };

  const handleArchive = async (id) => {
    try {
      await client.patch(`/admin/documents/${id}`, { status: 'archived' });
      fetchDocuments();
    } catch (err) {
      console.error(err);
      alert('Archive failed: ' + getErrorMessage(err));
    }
  };

  const handleDelete = async (id) => {
    try {
      await client.delete(`/admin/documents/${id}`);
      setDeleteConfirm({ id: null, filename: '', input: '' });
      fetchDocuments();
    } catch (err) {
      console.error(err);
      alert('Delete failed: ' + getErrorMessage(err));
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
      alert('Upload failed: ' + getErrorMessage(err));
    }
  };

  const renderStatusTag = (status, docId) => {
    const s = status ? status.toUpperCase() : 'UNKNOWN';
    let style = { padding: '4px 8px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '10px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' };
    
    if (s === 'ACTIVE' || s === 'INDEXED') {
      return <span style={{ ...style, background: '#dcfce7', color: '#15803d' }}>● ACTIVE</span>;
    } else if (s === 'PENDING_APPROVAL' || s === 'APPROVED') {
      return (
        <span 
          onClick={docId ? () => handleApprove(docId) : undefined}
          title={docId ? "Click to approve immediately" : undefined}
          style={{ ...style, background: '#fef3c7', color: '#b45309', cursor: docId ? 'pointer' : 'default', border: docId ? '1px dashed #f59e0b' : 'none' }}
        >
          ⏳ PENDING APPROVAL {docId ? '✓' : ''}
        </span>
      );
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
      return { color: '#15803d', icon: '✓' };
    } else if (currentIndex === stageIndex) {
      return { color: '#2563eb', icon: '○' };
    } else {
      return { color: '#94a3b8', icon: '○' };
    }
  };

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      
      {/* Top Header */}
      <header style={{ background: 'white', padding: '12px clamp(14px, 3vw, 24px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <a href="/chat" style={{ fontSize: '13px', color: '#2563eb', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', minHeight: '36px' }}>
            ← Back to Chat
          </a>
          <h1 style={{ fontSize: 'clamp(15px, 2.5vw, 18px)', fontWeight: 700, margin: 0, color: '#0f172a' }}>
            Knowledge Administration
          </h1>
          {user?.tenant_id && (
            <span style={{ fontSize: '11px', background: '#f1f5f9', color: '#475569', padding: '2px 8px', borderRadius: '12px', fontFamily: 'monospace' }}>
              Tenant: {user.tenant_id}
            </span>
          )}
        </div>
        <button 
          onClick={logout} 
          style={{ background: '#f1f5f9', color: '#475569', border: 'none', padding: '8px 14px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', minHeight: '36px' }}
        >
          Logout
        </button>
      </header>

      {/* Tabs Bar with smooth horizontal scrolling on mobile */}
      <nav style={{ padding: '0 clamp(14px, 3vw, 24px)', background: 'white', borderBottom: '1px solid #e2e8f0', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <div style={{ display: 'flex', gap: '20px', minWidth: 'max-content' }}>
          {['Documents', 'Upload', 'Unanswered Queries', 'Audit Logs', 'Analytics'].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                background: 'none',
                border: 'none',
                padding: '14px 4px',
                cursor: 'pointer',
                fontSize: '13px',
                borderBottom: activeTab === tab ? '2px solid #2563eb' : '2px solid transparent',
                color: activeTab === tab ? '#2563eb' : '#64748b',
                fontWeight: activeTab === tab ? 700 : 500,
                minHeight: '44px',
                whiteSpace: 'nowrap'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: 'clamp(12px, 3vw, 24px)', maxWidth: '1400px', width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
        
        {/* DOCUMENTS TAB */}
        {activeTab === 'Documents' && (
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Managed Documents ({documents.length})
              </div>
              <button
                onClick={() => setActiveTab('Upload')}
                style={{ background: '#2563eb', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', minHeight: '36px' }}
              >
                + Upload New Document
              </button>
            </div>
            
            {/* Scrollable table container */}
            <div className="responsive-table-wrap">
              <table style={{ width: '100%', minWidth: '780px', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '28%' }}>Title / Filename</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '18%' }}>Department</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '10%' }}>Authority</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '7%' }}>Ver</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '16%' }}>Status</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '9%' }}>Checksum</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '12%', textAlign: 'right', paddingRight: '20px' }}>Actions</th>
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
                      <td style={{ padding: '14px 16px' }}>{renderStatusTag(doc.status, doc.status === 'pending_approval' ? doc.id : null)}</td>
                      <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontSize: '11px', color: '#94a3b8' }}>
                        {doc.checksum ? `${doc.checksum.substring(0, 8)}...` : '-'}
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right', paddingRight: '20px' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                          {doc.status === 'pending_approval' && (
                            <button 
                              onClick={() => handleApprove(doc.id)} 
                              style={{ 
                                background: '#16a34a', 
                                color: 'white', 
                                border: 'none', 
                                padding: '6px 12px', 
                                borderRadius: '5px', 
                                fontSize: '11px', 
                                fontWeight: 700, 
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                minHeight: '32px'
                              }}
                              title="Approve Document for RAG indexing"
                            >
                              ✓ Approve
                            </button>
                          )}
                          {doc.status === 'active' && (
                            <button 
                              onClick={() => handleArchive(doc.id)} 
                              style={{ background: '#f8fafc', color: '#475569', border: '1px solid #cbd5e1', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 500, cursor: 'pointer', minHeight: '32px' }}
                              title="Archive Document"
                            >
                              Archive
                            </button>
                          )}
                          {doc.status === 'archived' && (
                            <button 
                              onClick={() => handleApprove(doc.id)} 
                              style={{ background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, cursor: 'pointer', minHeight: '32px' }}
                              title="Re-activate Document"
                            >
                              Activate
                            </button>
                          )}
                          
                          {deleteConfirm.id === doc.id ? (
                            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                              <button 
                                onClick={() => handleDelete(doc.id)} 
                                style={{ background: '#dc2626', color: 'white', border: 'none', padding: '6px 10px', fontSize: '11px', fontWeight: 600, borderRadius: '4px', cursor: 'pointer', minHeight: '32px' }}
                              >
                                Confirm?
                              </button>
                              <button 
                                onClick={() => setDeleteConfirm({ id: null, filename: '', input: '' })} 
                                style={{ background: '#f1f5f9', color: '#64748b', border: '1px solid #cbd5e1', padding: '6px 8px', fontSize: '11px', borderRadius: '4px', cursor: 'pointer', minHeight: '32px' }}
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button 
                              onClick={() => setDeleteConfirm({ id: doc.id, filename: doc.filename, input: '' })} 
                              style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', fontWeight: 600, minHeight: '32px' }}
                              title="Delete Document"
                            >
                              🗑 Delete
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
          </div>
        )}

        {/* UPLOAD TAB */}
        {activeTab === 'Upload' && (
          <div style={{ maxWidth: '680px', margin: '0 auto', width: '100%' }}>
            <div 
              style={{
                border: '2px dashed #cbd5e1', borderRadius: '8px', padding: 'clamp(20px, 4vw, 32px) 16px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: 'white', marginBottom: '20px', cursor: 'pointer', textAlign: 'center'
              }}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>📄</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '4px', wordBreak: 'break-word' }}>
                {file ? file.name : 'Choose a PDF document or tap here'}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                Official scheme guidelines, circulars, or policy documents
              </div>
              <input id="file-upload" type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} style={{ display: 'none' }} />
            </div>

            <form onSubmit={handleFileUpload} style={{ background: 'white', padding: 'clamp(16px, 3vw, 24px)', border: '1px solid #e2e8f0', borderRadius: '8px', marginBottom: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
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

              {/* Responsive grid for form fields */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                    Department
                  </label>
                  <input 
                    type="text" 
                    value={department} 
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. Agriculture & Farmers"
                    style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                    required
                  />
                </div>
                <div>
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

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: '14px', marginBottom: '14px' }}>
                <div>
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
                <div>
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
                style={{ width: '100%', background: '#2563eb', color: 'white', padding: '12px', borderRadius: '6px', fontWeight: 600, fontSize: '14px', border: 'none', opacity: !file ? 0.5 : 1, cursor: !file ? 'not-allowed' : 'pointer', minHeight: '44px' }}
              >
                Upload & Ingest Document
              </button>
            </form>

            {uploadStatus && uploadStatus !== 'idle' && (
              <div style={{ background: 'white', padding: '18px', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '14px' }}>Processing Pipeline Status</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '8px', fontSize: '11px', fontFamily: 'monospace', textAlign: 'center' }}>
                  {[
                    { key: 'stage1', label: 'Extracting' },
                    { key: 'stage2', label: 'Chunking' },
                    { key: 'stage3', label: 'Embedding' },
                    { key: 'stage4', label: 'Approval' }
                  ].map(stage => {
                    const style = getStageStyle(stage.key);
                    return (
                      <div key={stage.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', color: style.color, padding: '8px 4px', background: '#f8fafc', borderRadius: '6px' }}>
                        <div style={{ fontSize: '14px', fontWeight: 700 }}>{style.icon}</div>
                        <div style={{ textTransform: 'uppercase' }}>{stage.label}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* UNANSWERED QUERIES TAB */}
        {activeTab === 'Unanswered Queries' && (
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
              Queries Triggering Fallback / Unanswered ({queries.length})
            </div>
            <div className="responsive-table-wrap">
              <table style={{ width: '100%', minWidth: '480px', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>User Query</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600, width: '220px' }}>Timestamp</th>
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
          </div>
        )}

        {/* AUDIT LOGS TAB */}
        {activeTab === 'Audit Logs' && (
          <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                Security & Administrative Audit Logs ({auditLogs.length})
              </div>
              <button
                onClick={fetchAuditLogs}
                style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '6px 12px', fontSize: '12px', cursor: 'pointer', fontWeight: 600, color: '#334155', minHeight: '32px' }}
              >
                ↻ Refresh
              </button>
            </div>
            <div className="responsive-table-wrap">
              <table style={{ width: '100%', minWidth: '680px', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', background: '#f8fafc', fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>Event Type</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>Actor</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>Tenant</th>
                    <th style={{ padding: '12px 16px', fontWeight: 600 }}>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '12px' }}>
                      <td style={{ padding: '12px 16px', color: '#64748b', fontFamily: 'monospace' }}>{new Date(log.timestamp).toLocaleString()}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ 
                          padding: '3px 8px', 
                          borderRadius: '4px', 
                          fontWeight: 600, 
                          fontSize: '11px',
                          background: log.event_type && log.event_type.includes('BLOCKED') ? '#fee2e2' : '#e0f2fe',
                          color: log.event_type && log.event_type.includes('BLOCKED') ? '#b91c1c' : '#0369a1'
                        }}>
                          {log.event_type}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', color: '#0f172a', fontWeight: 500 }}>{log.user_id || 'anonymous'}</td>
                      <td style={{ padding: '12px 16px', color: '#64748b', fontFamily: 'monospace' }}>{log.tenant_id}</td>
                      <td style={{ padding: '12px 16px', color: '#334155', fontFamily: 'monospace', maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.details ? JSON.stringify(log.details) : log.ip_address || '-'}
                      </td>
                    </tr>
                  ))}
                  {auditLogs.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                        No audit events recorded for this tenant yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ANALYTICS TAB */}
        {activeTab === 'Analytics' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: '16px' }}>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Total Messages</div>
              <div style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700, color: '#0f172a' }}>{analytics?.total_messages ?? 0}</div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Conversations</div>
              <div style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700, color: '#0f172a' }}>{analytics?.total_conversations ?? 0}</div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Active Users</div>
              <div style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700, color: '#0f172a' }}>{analytics?.total_users ?? 0}</div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Indexed Documents</div>
              <div style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700, color: '#0f172a' }}>{analytics?.total_documents ?? 0}</div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>Fallback Rate</div>
              <div style={{ fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700, color: '#0f172a' }}>{((analytics?.fallback_rate ?? 0) * 100).toFixed(1)}%</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
