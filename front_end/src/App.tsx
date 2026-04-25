import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from './api';
import type { ChatMessage } from './api';
import './index.css';

interface MapItem {
  id: string;
  url: string;
  timestamp: number;
}

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([{
    role: 'agent',
    content: 'Hello! I am the HCDP Assistant. I can help map weather data for Hawaii. How can I assist you today?'
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [maps, setMaps] = useState<MapItem[]>([]);
  const [expandedMapId, setExpandedMapId] = useState<string | null>(null);
  
  const [sessionId] = useState<string>(() => {
    let sid = localStorage.getItem('hcdp_session_id');
    if (!sid || sid === 'default') {
      sid = Math.random().toString(36).substring(2, 11) + Math.random().toString(36).substring(2, 11);
      localStorage.setItem('hcdp_session_id', sid);
    }
    return sid;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage, sessionId);
      setMessages(response.messages);
      
      if (response.map_url) {
        const HOST = window.location.port === '5173' 
          ? `http://${window.location.hostname}:8000` 
          : `${window.location.protocol}//${window.location.host}/api`;
        
        const newUrl = `${HOST}${response.map_url}?t=${new Date().getTime()}`;
        const newMap: MapItem = {
          id: Math.random().toString(36).substring(7),
          url: newUrl,
          timestamp: Date.now()
        };
        setMaps(prev => [newMap, ...prev]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'agent', content: `Error communicating with server.` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const removeMap = (id: string) => {
    setMaps(prev => prev.filter(m => m.id !== id));
    if (expandedMapId === id) setExpandedMapId(null);
  };

  const clearAllMaps = () => {
    setMaps([]);
    setExpandedMapId(null);
  };

  const toggleExpand = (id: string) => {
    setExpandedMapId(expandedMapId === id ? null : id);
  };

  const downloadMap = (url: string) => {
    const link = document.createElement('a');
    link.href = url;
    // Extract filename or use timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.download = `hcdp_map_${timestamp}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const expandedMap = maps.find(m => m.id === expandedMapId);

  return (
    <div className="app-container">
      {/* Chat Section */}
      <div className="panel chat-section">
        <div className="chat-header">
          <h1>HCDP AI Assistant</h1>
          <p>Climate & Weather Data Explorer</p>
        </div>
        
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <form onSubmit={handleSubmit} className="input-container">
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="E.g., Map rainfall near Honolulu..."
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={isLoading || input.trim() === ''}>
              Send
            </button>
          </form>
        </div>
      </div>

      {/* Map Section */}
      <div className="panel map-section">
        <div className="map-header-container">
          <div className="map-header">
            {maps.length > 0 ? `Interactive Maps (${maps.length})` : 'Map View'}
          </div>
          {maps.length > 0 && (
            <button className="clear-maps-btn" onClick={clearAllMaps}>
              Clear All
            </button>
          )}
        </div>
        
        {maps.length > 0 ? (
          <div className={`map-grid ${maps.length === 1 || expandedMapId ? 'single' : maps.length === 2 ? 'dual' : 'multi'}`}>
            {/* If a map is expanded, only show that one, otherwise show the grid */}
            {(expandedMapId && expandedMap ? [expandedMap] : maps).map((map) => (
              <div key={map.id} className={`map-wrapper ${expandedMapId === map.id ? 'expanded' : ''}`}>
                <div className="map-label">
                  Map {maps.length - (maps.indexOf(map))}
                </div>
                <div className="map-controls">
                  <button className="map-btn download-btn" onClick={() => downloadMap(map.url)}>
                    Download
                  </button>
                  <button className="map-btn expand-btn" onClick={() => toggleExpand(map.id)}>
                    {expandedMapId === map.id ? 'Exit Fullscreen' : 'Expand'}
                  </button>
                  <button className="map-btn delete-btn" onClick={() => removeMap(map.id)}>
                    Remove
                  </button>
                </div>
                <iframe src={map.url} className="map-frame" title={`Map ${map.id}`} />
              </div>
            ))}
          </div>
        ) : (
          <div className="map-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
              <line x1="9" y1="3" x2="9" y2="18"></line>
              <line x1="15" y1="6" x2="15" y2="21"></line>
            </svg>
            <p>Ask the assistant to generate maps to see them here</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
