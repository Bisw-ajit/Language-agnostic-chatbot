import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function ChatPage() {
  const { logout, role } = useContext(AuthContext);
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(''); // '' means Auto-detect
  const [expandedSourceId, setExpandedSourceId] = useState(null);
  const [feedbackDialogMsgId, setFeedbackDialogMsgId] = useState(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversationId) {
      fetchMessages(selectedConversationId);
    } else {
      setMessages([]);
    }
  }, [selectedConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchConversations = async () => {
    try {
      const res = await client.get('/conversations');
      setConversations(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMessages = async (id) => {
    try {
      const res = await client.get(`/conversations/${id}/messages`);
      setMessages(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleNewConversation = () => {
    setSelectedConversationId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      await client.delete(`/conversations/${convId}`);
      if (selectedConversationId === convId) {
        setSelectedConversationId(null);
        setMessages([]);
      }
      fetchConversations();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (queryText) => {
    const textToSend = queryText || inputValue;
    if (!textToSend || !textToSend.trim()) return;
    
    setInputValue('');
    
    // Optimistic UI for user message
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const payload = { 
        message: textToSend,
        preferred_language: selectedLanguage || undefined
      };
      if (selectedConversationId) {
        payload.conversation_id = selectedConversationId;
      }
      
      const res = await client.post('/chat', payload);
      
      if (!selectedConversationId && res.data.conversation_id) {
        setSelectedConversationId(res.data.conversation_id);
        fetchConversations();
      }
      
      setMessages(prev => [...prev, res.data]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: 'An error occurred while contacting the server. Please try again.',
          is_fallback: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFeedback = async (messageId, rating) => {
    try {
      await client.post('/feedback', { 
        message_id: messageId, 
        rating: rating,
        comment: feedbackComment || undefined
      });
      setMessages(prev => prev.map(m => m.id === messageId ? { ...m, feedback_rating: rating } : m));
      setFeedbackDialogMsgId(null);
      setFeedbackComment('');
    } catch (err) {
      console.error(err);
    }
  };

  const samplePrompts = [
    { title: "KALIA Scheme (English)", text: "What are the eligibility criteria and benefits for KALIA Yojana?" },
    { title: "BSKY Health (Hinglish)", text: "BSKY me kitna cashless treatment milta hai aur kaunse documents chahiye?" },
    { title: "Madhu Babu Pension (Odia)", text: "ମଧୁ ବାବୁ ପେନସନ ଯୋଜନା ପାଇଁ କଣ ଯୋଗ୍ୟତା ଏବଂ କେତେ ଟଙ୍କା ମିଳେ?" },
    { title: "Scholarship Scheme (Hindi)", text: "ओडिशा स्टेट स्कॉलरशिप योजना की अंतिम तिथि और पात्रता क्या है?" }
  ];

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', fontFamily: 'Inter, sans-serif', background: '#f8fafc' }}>
      
      {/* SIDEBAR */}
      <div style={{ width: '280px', background: '#0f172a', color: '#f8fafc', display: 'flex', flexDirection: 'column', borderRight: '1px solid #1e293b' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ fontSize: '20px' }}>🏛️</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '15px', color: '#ffffff' }}>Odisha Info Desk</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Multilingual RAG Assistant</div>
            </div>
          </div>
          <button 
            onClick={handleNewConversation}
            style={{ width: '100%', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', padding: '10px 14px', fontWeight: 600, fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
          >
            <span>+</span> New Conversation
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', padding: '8px 12px', letterSpacing: '0.5px' }}>
            Recent Conversations
          </div>
          {conversations.map(conv => {
            const isSelected = selectedConversationId === conv.id;
            return (
              <div 
                key={conv.id}
                onClick={() => setSelectedConversationId(conv.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  marginBottom: '4px',
                  background: isSelected ? '#1e293b' : 'transparent',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'background 0.15s'
                }}
              >
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '13px', color: isSelected ? '#ffffff' : '#cbd5e1', flex: 1 }}>
                  💬 {conv.last_message || 'New Conversation'}
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '14px', padding: '2px 4px' }}
                  title="Delete conversation"
                >
                  ✕
                </button>
              </div>
            );
          })}
          {conversations.length === 0 && (
            <div style={{ padding: '16px 12px', fontSize: '12px', color: '#64748b', textAlign: 'center' }}>
              No previous chats yet.
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div style={{ padding: '16px', borderTop: '1px solid #1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0' }}>Role: {role?.toUpperCase()}</div>
            {role === 'admin' && (
              <button 
                onClick={() => navigate('/admin')}
                style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '12px', padding: 0, cursor: 'pointer', textDecoration: 'underline', marginTop: '4px' }}
              >
                Go to Admin Portal →
              </button>
            )}
          </div>
          <button 
            onClick={logout}
            style={{ background: '#334155', border: 'none', color: '#f8fafc', padding: '6px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        
        {/* TOP HEADER */}
        <header style={{ height: '60px', background: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontWeight: 700, fontSize: '16px', color: '#0f172a' }}>Official Knowledge Assistant</span>
            <span style={{ fontSize: '11px', background: '#e0f2fe', color: '#0369a1', padding: '3px 8px', borderRadius: '12px', fontWeight: 600 }}>
              Grounded & Anti-Hallucination
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <label style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>Target Language:</label>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#ffffff', fontSize: '13px', fontWeight: 500, color: '#0f172a' }}
            >
              <option value="">⚡ Auto-Detect</option>
              <option value="en">English</option>
              <option value="hi">हिन्दी (Hindi)</option>
              <option value="hi-en">Hinglish (Hindi in Latin)</option>
              <option value="or">ଓଡ଼ିଆ (Odia)</option>
            </select>
          </div>
        </header>

        {/* CHAT MESSAGES SCROLL AREA */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', background: '#f8fafc' }}>
          <div style={{ maxWidth: '840px', margin: '0 auto' }}>
            
            {/* WELCOME / STARTER CHIPS */}
            {messages.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>🇮🇳 📜</div>
                <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
                  Ask About Odisha Government Schemes
                </h2>
                <p style={{ fontSize: '14px', color: '#64748b', maxWidth: '520px', margin: '0 auto 28px auto' }}>
                  Ask questions in English, Hindi, Hinglish, or Odia. The assistant answers strictly from official scheme records with citations.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', textAlign: 'left' }}>
                  {samplePrompts.map((p, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSend(p.text)}
                      style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', cursor: 'pointer', boxShadow: '0 2px 4px rgba(0,0,0,0.02)', transition: 'all 0.15s' }}
                      onMouseEnter={(e) => e.currentTarget.style.borderColor = '#2563eb'}
                      onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
                    >
                      <div style={{ fontSize: '11px', fontWeight: 600, color: '#2563eb', textTransform: 'uppercase', marginBottom: '6px' }}>
                        {p.title}
                      </div>
                      <div style={{ fontSize: '13px', color: '#334155', lineHeight: 1.4 }}>
                        "{p.text}"
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* MESSAGE LIST */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {messages.map((msg, idx) => {
                const isUser = msg.role === 'user';
                const hasSources = msg.sources && msg.sources.length > 0;
                const isFallback = msg.is_fallback;

                if (isUser) {
                  return (
                    <div key={msg.id || idx} style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <div style={{ background: '#1e293b', color: '#ffffff', padding: '14px 18px', borderRadius: '12px 12px 2px 12px', maxWidth: '75%', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
                        <div style={{ fontSize: '14px', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                        <div style={{ fontSize: '10px', color: '#94a3b8', textAlign: 'right', marginTop: '6px' }}>
                          {new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={msg.id || idx} style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div style={{ background: '#ffffff', border: isFallback ? '1px solid #fecaca' : '1px solid #e2e8f0', borderRadius: '12px 12px 12px 2px', padding: '18px', maxWidth: '85%', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                      
                      {/* Message Meta Header */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                        {msg.language_display && (
                          <span style={{ fontSize: '10px', background: '#f1f5f9', color: '#475569', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                            {msg.language_display}
                          </span>
                        )}
                        {msg.evidence_level && (
                          <span style={{ 
                            fontSize: '10px', 
                            background: msg.evidence_level === 'HIGH' ? '#dcfce7' : msg.evidence_level === 'MEDIUM' ? '#fef3c7' : '#fee2e2', 
                            color: msg.evidence_level === 'HIGH' ? '#15803d' : msg.evidence_level === 'MEDIUM' ? '#b45309' : '#b91c1c', 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            fontWeight: 600 
                          }}>
                            {isFallback ? 'UNVERIFIED / FALLBACK' : `EVIDENCE: ${msg.evidence_level}`}
                          </span>
                        )}
                        {msg.confidence !== undefined && (
                          <span style={{ fontSize: '10px', background: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                            CONFIDENCE: {(msg.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>

                      {/* Content */}
                      <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#0f172a', whiteSpace: 'pre-wrap' }}>
                        {msg.content}
                      </div>

                      {/* Source Citations Drawer */}
                      {hasSources && (
                        <div style={{ marginTop: '16px', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                            Verified Source Citations ({msg.sources.length})
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {msg.sources.map((src, sIdx) => {
                              const isExpanded = expandedSourceId === `${msg.id}_${sIdx}`;
                              const authBadgeColor = src.authority_level === 'official' ? { bg: '#dcfce7', text: '#15803d' }
                                : src.authority_level === 'demo' ? { bg: '#f3e8ff', text: '#7e22ce' }
                                : src.authority_level === 'trusted' ? { bg: '#e0f2fe', text: '#0369a1' }
                                : { bg: '#ffedd5', text: '#c2410c' };

                              return (
                                <div key={sIdx} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px 12px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: '#1e293b' }}>
                                      <span>📄 {src.document_title || src.title || src.source}</span>
                                      <span style={{ fontSize: '9px', background: authBadgeColor.bg, color: authBadgeColor.text, padding: '1px 5px', borderRadius: '3px', fontWeight: 700, textTransform: 'uppercase' }}>
                                        {src.authority_level || 'OFFICIAL'}
                                      </span>
                                      {src.version && (
                                        <span style={{ fontSize: '9px', background: '#f1f5f9', color: '#475569', padding: '1px 5px', borderRadius: '3px', fontWeight: 600 }}>
                                          v{src.version}
                                        </span>
                                      )}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      {src.source_url && (
                                        <a 
                                          href={src.source_url} 
                                          target="_blank" 
                                          rel="noreferrer"
                                          style={{ fontSize: '11px', color: '#0284c7', textDecoration: 'none', fontWeight: 500 }}
                                        >
                                          🔗 Link
                                        </a>
                                      )}
                                      <button
                                        onClick={() => setExpandedSourceId(isExpanded ? null : `${msg.id}_${sIdx}`)}
                                        style={{ background: 'none', border: 'none', color: '#2563eb', fontSize: '11px', fontWeight: 600, cursor: 'pointer' }}
                                      >
                                        {isExpanded ? 'Hide Excerpt ▲' : 'View Excerpt ▼'}
                                      </button>
                                    </div>
                                  </div>
                                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '3px' }}>
                                    {src.department} · {src.section || 'General'} · Pg. {src.page}
                                  </div>
                                  {isExpanded && (
                                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#475569', fontStyle: 'italic', background: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                                      "{src.excerpt}"
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Feedback & Actions */}
                      <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleFeedback(msg.id, 'up')}
                            style={{ background: msg.feedback_rating === 'up' ? '#dcfce7' : '#f1f5f9', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                            title="Helpful"
                          >
                            👍 Helpful
                          </button>
                          <button
                            onClick={() => {
                              setFeedbackDialogMsgId(msg.id);
                              handleFeedback(msg.id, 'down');
                            }}
                            style={{ background: msg.feedback_rating === 'down' ? '#fee2e2' : '#f1f5f9', border: 'none', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                            title="Not Helpful"
                          >
                            👎 Incorrect / Missing info
                          </button>
                        </div>
                      </div>

                      {/* Feedback comment input modal/box */}
                      {feedbackDialogMsgId === msg.id && (
                        <div style={{ marginTop: '10px', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '10px', borderRadius: '6px' }}>
                          <div style={{ fontSize: '12px', color: '#475569', marginBottom: '6px' }}>
                            Help us improve: What was incorrect or missing in this answer?
                          </div>
                          <input
                            type="text"
                            value={feedbackComment}
                            onChange={(e) => setFeedbackComment(e.target.value)}
                            placeholder="e.g. Missing required document list or incorrect amount"
                            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box', marginBottom: '8px' }}
                          />
                          <button
                            onClick={() => handleFeedback(msg.id, 'down')}
                            style={{ background: '#0f172a', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                          >
                            Submit Feedback
                          </button>
                        </div>
                      )}

                    </div>
                  </div>
                );
              })}

              {/* Loading Indicator */}
              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 20px', color: '#64748b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span> Retrieving official documents and validating facts...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

          </div>
        </div>

        {/* INPUT BAR */}
        <div style={{ background: '#ffffff', borderTop: '1px solid #e2e8f0', padding: '16px 24px' }}>
          <div style={{ maxWidth: '840px', margin: '0 auto' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything in English, Hindi, Hinglish, or Odia..."
                style={{ flex: 1, resize: 'none', minHeight: '48px', maxHeight: '120px', padding: '12px 16px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
                rows={1}
              />
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || loading}
                style={{ background: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '8px', height: '48px', padding: '0 24px', fontWeight: 600, fontSize: '14px', cursor: (!inputValue.trim() || loading) ? 'not-allowed' : 'pointer', opacity: (!inputValue.trim() || loading) ? 0.6 : 1 }}
              >
                Send
              </button>
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', textAlign: 'center' }}>
              Supports English, हिन्दी (Devanagari), Hinglish (Latin), and ଓଡ଼ିଆ (Odia) with strict source citations.
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

