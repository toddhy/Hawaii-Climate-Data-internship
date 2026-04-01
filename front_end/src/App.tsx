import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from './api';
import type { ChatMessage } from './api';
import './index.css';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([{
    role: 'agent',
    content: 'Hello! I am the HCDP Assistant. I can help map nearby weather stations or generate gridded rainfall maps for Hawaii. How can I assist you today?'
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [mapUrl, setMapUrl] = useState<string | null>(null);
  const [sessionId] = useState<string>(() => {
    let sid = localStorage.getItem('hcdp_session_id');
    if (!sid) {
      sid = Math.random().toString(36).substring(2, 11) + Math.random().toString(36).substring(2, 11);
      localStorage.setItem('hcdp_session_id', sid);
    }
    return sid;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
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
      
      // The API returns all messages, but we only want to append the new ones that aren't the user message we just added
      // Or simply replace the entire message history
      setMessages(response.messages);
      
      if (response.map_url) {
        // use absolute URL based on API base to render iframe correctly
        const HOST = window.location.port === '5173' 
          ? `http://${window.location.hostname}:8000` 
          : `${window.location.protocol}//${window.location.host}/api`;
        setMapUrl(`${HOST}${response.map_url}?t=${new Date().getTime()}`);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: `Sorry, I encountered an error communicating with the server.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

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
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
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
        {mapUrl && (
          <div className="map-header">
            Interactive Map View
          </div>
        )}
        
        {mapUrl ? (
          <iframe 
            src={mapUrl} 
            className="map-frame" 
            title="Generated Map"
          />
        ) : (
          <div className="map-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
              <line x1="9" y1="3" x2="9" y2="18"></line>
              <line x1="15" y1="6" x2="15" y2="21"></line>
            </svg>
            <p>Ask the assistant to generate a map to see it displayed here</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
