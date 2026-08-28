import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../App';
import client from '../api/client';

export default function ChatPage() {
  const { logout } = useContext(AuthContext);
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedExcerptId, setExpandedExcerptId] = useState(null);
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

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const currentInput = inputValue;
    setInputValue('');
    
    // Optimistic UI for user message
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: currentInput,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const payload = { message: currentInput };
      if (selectedConversationId) {
        payload.conversation_id = selectedConversationId;
      }
      
      const res = await client.post('/chat', payload);
      
      if (!selectedConversationId && res.data.conversation_id) {
        setSelectedConversationId(res.data.conversation_id);
        fetchConversations(); // refresh list
      }
      
      // Update with server response (which might include both user and bot messages, or just bot)
      // Usually chat endpoints return the bot message or full thread. Let's assume it returns the bot message.
      setMessages(prev => [...prev, res.data]);
    } catch (err) {
      console.error(err);
      // Optional: add error message to chat
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

  const handleFeedback = async (messageId, isPositive) => {
    try {
      await client.post('/feedback', { message_id: messageId, is_positive: isPositive });
      // Update message visually
      setMessages(prev => prev.map(m => m.id === messageId ? { ...m, feedback: isPositive } : m));
    } catch (err) {
      console.error(err);
    }
  };

  const lastBotMessage = messages.filter(m => m.role === 'assistant' || m.role === 'bot').pop();
  const languageDisplay = lastBotMessage?.language_display || 'ENGLISH';

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* LEFT RAIL */}
      <div style={{ width: '240px', background: 'white', borderRight: '1px solid var(--slate-line)', display: 'flex', flexDirection: 'column', position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 10 }}>
        <div style={{ padding: '16px' }}>
          <button 
            onClick={handleNewConversation}
            style={{ width: '100%', background: 'var(--ink-indigo)', color: 'white', borderRadius: '4px', padding: '10px', marginBottom: '8px', fontWeight: 500 }}
          >
            + New Conversation
          </button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {conversations.map(conv => {
            const isSelected = selectedConversationId === conv.id;
            return (
              <div 
                key={conv.id}
                onClick={() => setSelectedConversationId(conv.id)}
                style={{
                  padding: '12px 16px',
                  cursor: 'pointer',
                  borderLeft: isSelected ? '3px solid var(--turmeric-gold)' : '3px solid transparent',
                  background: isSelected ? 'rgba(217, 166, 46, 0.1)' : 'transparent'
                }}
              >
                <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--ink-indigo)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {conv.last_message || 'New Conversation'}
                </div>
                {conv.updated_at && (
                  <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '10px', color: 'var(--slate-line)', marginTop: '4px' }}>
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, marginLeft: '240px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
        
        {/* HEADER */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', background: 'white', borderBottom: '1px solid var(--slate-line)', position: 'sticky', top: 0, zIndex: 10 }}>
          <div style={{ fontFamily: 'Fraunces', fontSize: '16px', fontWeight: 600 }}>
            Institutional Information Desk
          </div>
          <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '11px', border: '1px solid var(--turmeric-gold)', color: 'var(--turmeric-gold)', padding: '2px 8px', borderRadius: '2px', textTransform: 'uppercase' }}>
            {languageDisplay}
          </div>
          <button onClick={logout} style={{ background: 'transparent', color: 'var(--ink-indigo)', fontSize: '14px', fontWeight: 500 }}>
            Logout
          </button>
        </header>

        {/* THREAD */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', background: 'var(--mist-paper)' }}>
          {messages.length === 0 && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
              {['What is the scholarship deadline?', 'छात्रवृत्ति के लिए क्या दस्तावेज चाहिए?', 'Hostel ka last date kya hai?'].map((chip, idx) => (
                <div 
                  key={idx}
                  onClick={() => setInputValue(chip)}
                  style={{
                    background: 'white', border: '1px solid var(--slate-line)', borderRadius: '4px', padding: '12px 20px', cursor: 'pointer', fontFamily: 'Inter', fontSize: '14px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                  }}
                >
                  {chip}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px', margin: '0 auto' }}>
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              if (isUser) {
                return (
                  <div key={msg.id || idx} style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <div style={{ background: 'white', borderLeft: '3px solid var(--ink-indigo)', padding: '14px 18px', maxWidth: '65%', borderRadius: '4px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                      <div style={{ fontSize: '15px', lineHeight: '1.5' }}>{msg.content}</div>
                      <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)', textAlign: 'right', marginTop: '8px' }}>
                        {new Date(msg.created_at || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </div>
                    </div>
                  </div>
                );
              } else {
                const hasSource = msg.sources && msg.sources.length > 0;
                const isFallback = msg.is_fallback;
                
                return (
                  <div key={msg.id || idx} style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div style={{ background: 'white', borderLeft: isFallback ? '3px solid var(--alert-rust)' : '3px solid var(--turmeric-gold)', padding: '14px 18px', maxWidth: '65%', borderRadius: '4px', position: 'relative', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                      <div style={{ fontSize: '15px', lineHeight: '1.5', marginBottom: '28px' }}>{msg.content}</div>
                      
                      {/* Stamp Badge */}
                      {!isFallback && hasSource ? (
                        <div 
                          onClick={() => setExpandedExcerptId(expandedExcerptId === msg.id ? null : msg.id)}
                          style={{
                            position: 'absolute', bottom: '8px', right: '8px', display: 'inline-block', border: '1px solid var(--turmeric-gold)', boxShadow: 'inset 0 0 0 2px var(--turmeric-gold)', color: 'var(--turmeric-gold)', fontFamily: 'IBM Plex Mono', fontSize: '9px', textTransform: 'uppercase', padding: '3px 8px', transform: 'rotate(-2deg)', cursor: 'pointer'
                          }}
                        >
                          {msg.sources[0].source} · P.{msg.sources[0].page}
                        </div>
                      ) : isFallback ? (
                        <div style={{
                          position: 'absolute', bottom: '8px', right: '8px', display: 'inline-block', border: '1px dashed var(--alert-rust)', color: 'var(--alert-rust)', fontFamily: 'IBM Plex Mono', fontSize: '9px', textTransform: 'uppercase', padding: '3px 8px'
                        }}>
                          UNVERIFIED — NO SOURCE FOUND
                        </div>
                      ) : null}

                      {/* Feedback */}
                      <div style={{ position: 'absolute', bottom: '8px', left: '18px', display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => handleFeedback(msg.id, true)} 
                          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px', color: msg.feedback === true ? 'var(--banyan-green)' : 'var(--slate-line)' }}
                        >👍</button>
                        <button 
                          onClick={() => handleFeedback(msg.id, false)} 
                          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '12px', color: msg.feedback === false ? 'var(--alert-rust)' : 'var(--slate-line)' }}
                        >👎</button>
                      </div>

                      {expandedExcerptId === msg.id && hasSource && (
                        <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--slate-line)', fontSize: '12px', color: 'var(--slate-line)', fontStyle: 'italic' }}>
                          "{msg.sources[0].excerpt}"
                        </div>
                      )}
                    </div>
                  </div>
                );
              }
            })}
            
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ background: 'white', borderLeft: '3px solid var(--slate-line)', padding: '14px 18px', borderRadius: '4px', color: 'var(--slate-line)', fontFamily: 'IBM Plex Mono', fontSize: '20px', lineHeight: 1 }}>
                  ···
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* COMPOSER */}
        <div style={{ background: 'white', borderTop: '1px solid var(--slate-line)', padding: '16px' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message..."
                style={{ flex: 1, resize: 'none', minHeight: '44px', padding: '12px', border: '1px solid var(--slate-line)', borderRadius: '4px', fontSize: '15px', outline: 'none' }}
                rows={1}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || loading}
                style={{ background: 'var(--ink-indigo)', color: 'white', borderRadius: '4px', height: '44px', padding: '0 24px', fontWeight: 600, opacity: (!inputValue.trim() || loading) ? 0.7 : 1 }}
              >
                Send
              </button>
            </div>
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '11px', color: 'var(--slate-line)', textAlign: 'left' }}>
              Ask in any language — English, Hindi, Hinglish, Odia
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
