export interface ChatMessage {
  role: 'user' | 'agent' | 'tool';
  content: string;
}

export interface ChatResponse {
  response: string;
  map_url: string | null;
  messages: ChatMessage[];
}

// In development, we use port 8000. In production (via Nginx), we can use the same host.
const API_BASE_URL = window.location.port === '5173' 
  ? `http://${window.location.hostname}:8000` 
  : `${window.location.protocol}//${window.location.host}/api`;

export async function sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  
  return res.json();
}
