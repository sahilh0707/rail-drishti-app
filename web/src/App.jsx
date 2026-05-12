import { useState, useRef, useEffect } from 'react';
import { Train, MessageSquare, Send, Activity, Clock, MapPin, Calendar, CheckCircle, ChevronDown, Bot, User, Sparkles } from 'lucide-react';
import './index.css';

// In dev, Vite proxies /api → FastAPI (vite.config.js). Set VITE_API_URL for production builds.
const API_URL = (import.meta.env.VITE_API_URL?.trim?.() || (import.meta.env.DEV ? '/api' : 'http://127.0.0.1:8000/api'));

function App() {
  const [activeTab, setActiveTab] = useState('predict');
  
  return (
    <div className="app-container">
      <header className="header">
        <h1>Rail-Drishti</h1>
        <p>Intelligent Railway Assistance Platform</p>
      </header>

      <div className="tabs">
        <button 
          className={`tab-btn ${activeTab === 'predict' ? 'active' : ''}`}
          onClick={() => setActiveTab('predict')}
        >
          <Activity size={20} />
          Delay Predictor
        </button>
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={20} />
          Railway Assistant
        </button>
      </div>

      <main>
        {/* Keep both mounted so chat history survives tab switches */}
        <div style={{ display: activeTab === 'predict' ? 'block' : 'none' }} aria-hidden={activeTab !== 'predict'}>
          <Predictor />
        </div>
        <div style={{ display: activeTab === 'chat' ? 'block' : 'none' }} aria-hidden={activeTab !== 'chat'}>
          <Chatbot />
        </div>
      </main>
    </div>
  );
}

function Predictor() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [trainOptions, setTrainOptions] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  
  const [formData, setFormData] = useState({
    Train_id: '',
    Train_name: '',
    Train_no: '',
    Source: '',
    Destitnation: '',
    Distance_Km: 0,
    Sc_arr__time: '10:00',
    Season: 'Winter',
    Run_frequency: 'Daliy',
    Date: new Date().toISOString().split('T')[0]
  });

  // Fetch train options on mount
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await fetch(`${API_URL}/train-options`);
        if (!response.ok) {
          throw new Error(`Backend HTTP ${response.status}`);
        }
        const data = await response.json();
        const trains = Array.isArray(data.trains) ? data.trains : [];
        if (data.success && trains.length > 0) {
          setTrainOptions(trains);
          const first = trains[0];
          setFormData(prev => ({
            ...prev,
            Train_id: first.Train_id,
            Train_name: first.Train_name,
            Train_no: first.Train_no,
            Source: first.Source,
            Destitnation: first.Destitnation,
            Distance_Km: first.Distance_Km,
            Sc_arr__time: first.Sc_arr__time,
            Run_frequency: first.Run_frequency,
          }));
        } else {
          setError(
            trains.length === 0
              ? 'No trains in dataset — check data/indian_railway_data.csv and backend logs.'
              : (data.error || 'Train list request failed.')
          );
        }
      } catch (err) {
        console.error('Failed to load train options:', err);
        setError('Could not load train options. Start the API: python -m uvicorn backend.main:app --port 8000 (from project root).');
      } finally {
        setLoadingOptions(false);
      }
    };
    fetchOptions();
  }, []);

  const handleTrainSelect = (e) => {
    const selectedName = e.target.value;
    const train = trainOptions.find(t => t.Train_name === selectedName);
    if (train) {
      setFormData(prev => ({
        ...prev,
        Train_id: train.Train_id,
        Train_name: train.Train_name,
        Train_no: train.Train_no,
        Source: train.Source,
        Destitnation: train.Destitnation,
        Distance_Km: train.Distance_Km,
        Sc_arr__time: train.Sc_arr__time,
        Run_frequency: train.Run_frequency,
      }));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'Distance_Km' ? parseFloat(value) : value
    }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data.delay_minutes);
      } else {
        setError(data.error || 'Failed to predict delay');
      }
    } catch (err) {
      setError('Could not connect to the prediction server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Train /> Train Delay Predictor
      </h2>
      
      <form onSubmit={handlePredict}>
        {/* Train Selection Dropdown */}
        <div className="train-select-section">
          <div className="input-group" style={{ maxWidth: '100%' }}>
            <label><Train size={14} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />Select Train</label>
            <div className="select-wrapper">
              <select 
                value={formData.Train_name} 
                onChange={handleTrainSelect} 
                className="neumorph-input train-dropdown"
                disabled={loadingOptions}
                id="train-select"
              >
                {loadingOptions ? (
                  <option>Loading trains...</option>
                ) : trainOptions.length === 0 ? (
                  <option>No trains available</option>
                ) : (
                  trainOptions.map((train, i) => (
                    <option key={i} value={train.Train_name}>
                      {train.Train_name} (#{train.Train_no}) — {train.Source} → {train.Destitnation}
                    </option>
                  ))
                )}
              </select>
              <ChevronDown size={18} className="select-icon" />
            </div>
          </div>
        </div>

        {/* Auto-filled train info cards */}
        {formData.Train_name && (
          <div className="train-info-cards">
            <div className="info-card">
              <span className="info-label">Train No</span>
              <span className="info-value">{formData.Train_no}</span>
            </div>
            <div className="info-card">
              <span className="info-label">Source</span>
              <span className="info-value">{formData.Source}</span>
            </div>
            <div className="info-card">
              <span className="info-label">Destination</span>
              <span className="info-value">{formData.Destitnation}</span>
            </div>
            <div className="info-card">
              <span className="info-label">Distance</span>
              <span className="info-value">{formData.Distance_Km} Km</span>
            </div>
            <div className="info-card">
              <span className="info-label">Scheduled Arrival</span>
              <span className="info-value">{formData.Sc_arr__time}</span>
            </div>
            <div className="info-card">
              <span className="info-label">Frequency</span>
              <span className="info-value">{formData.Run_frequency}</span>
            </div>
          </div>
        )}

        {/* User-editable fields */}
        <div className="form-grid" style={{ marginTop: '1.5rem' }}>
          <div className="input-group">
            <label><Calendar size={14} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />Travel Date</label>
            <input 
              type="date" 
              name="Date" 
              value={formData.Date} 
              onChange={handleChange} 
              className="neumorph-input" 
              required 
              id="travel-date"
            />
          </div>
          <div className="input-group">
            <label><Sparkles size={14} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />Season</label>
            <div className="select-wrapper">
              <select 
                name="Season" 
                value={formData.Season} 
                onChange={handleChange} 
                className="neumorph-input"
                id="season-select"
              >
                <option value="Summer">Summer</option>
                <option value="Monsoon">Monsoon</option>
                <option value="Winter">Winter</option>
                <option value="Spring">Spring</option>
              </select>
              <ChevronDown size={18} className="select-icon" />
            </div>
          </div>
        </div>
        
        <button type="submit" className="action-btn" disabled={loading || loadingOptions} id="predict-btn">
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
               <Activity className="animate-spin" /> Analyzing...
            </span>
          ) : (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle /> Predict Delay
            </span>
          )}
        </button>
      </form>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {result !== null && (
        <div className="result-box">
          <p>Predicted Delay Time</p>
          <h3>{result.toFixed(1)} Minutes</h3>
          <p style={{ marginTop: '0.5rem', color: result > 30 ? '#ff6b6b' : result > 10 ? '#ffd93d' : '#6bff9e' }}>
            {result > 30 ? '⚠ Significant Delay Expected' 
              : result > 10 ? '⏳ Moderate Delay Expected' 
              : '✅ Train is expected to be on time'}
          </p>
        </div>
      )}
    </div>
  );
}

function Chatbot() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hello! I'm **Rail Drishti AI** 🚂 — your intelligent Indian Railways assistant.\n\nI can help you with:\n• Railway rules & policies\n• Cancellation & refund info\n• Train schedules & delay data\n• General & Safety regulations\n• Or just chat about anything!\n\nHow can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setMessages(prev => [...prev, { role: 'bot', text: data.message }]);
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: `❌ Error: ${data.error || 'Something went wrong'}` }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', text: "Could not connect to the backend server. Please make sure it's running on port 8000." }]);
    } finally {
      setLoading(false);
    }
  };

  // Simple markdown renderer for bold, bullets, headers
  const renderMarkdown = (text) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    return lines.map((line, i) => {
      // Headers
      if (line.startsWith('### ')) {
        return <h4 key={i} className="chat-heading">{renderInline(line.slice(4))}</h4>;
      }
      if (line.startsWith('## ')) {
        return <h3 key={i} className="chat-heading">{renderInline(line.slice(3))}</h3>;
      }
      if (line.startsWith('# ')) {
        return <h2 key={i} className="chat-heading">{renderInline(line.slice(2))}</h2>;
      }
      // Bullet points
      if (line.match(/^[\s]*[-•*]\s/)) {
        return <div key={i} className="chat-bullet">{renderInline(line.replace(/^[\s]*[-•*]\s/, ''))}</div>;
      }
      // Numbered lists
      if (line.match(/^[\s]*\d+\.\s/)) {
        return <div key={i} className="chat-bullet">{renderInline(line)}</div>;
      }
      // Empty line = spacing
      if (line.trim() === '') {
        return <div key={i} style={{ height: '0.5rem' }} />;
      }
      // Regular paragraph
      return <p key={i} className="chat-para">{renderInline(line)}</p>;
    });
  };

  const renderInline = (text) => {
    // Bold: **text**
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  // Suggested prompts
  const suggestions = [
    "What are the cancellation rules?",
    "Tell me about luggage policies",
    "Which train has the most delays?",
    "What ID is needed for travel?"
  ];

  return (
    <div className="glass-panel chat-container">
      <div className="chat-history" id="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="msg-avatar">
              {msg.role === 'bot' ? <Bot size={18} /> : <User size={18} />}
            </div>
            <div className="msg-content">
              {msg.role === 'bot' ? renderMarkdown(msg.text) : <p className="chat-para">{msg.text}</p>}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg bot">
            <div className="msg-avatar"><Bot size={18} /></div>
            <div className="msg-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Suggestion chips (only show if there's just the welcome message) */}
      {messages.length === 1 && (
        <div className="suggestion-chips">
          {suggestions.map((s, i) => (
            <button 
              key={i} 
              className="chip" 
              onClick={() => { setInput(s); }}
              id={`suggestion-${i}`}
            >
              {s}
            </button>
          ))}
        </div>
      )}
      
      <form onSubmit={handleSend} className="chat-input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything about Indian Railways..." 
          className="neumorph-input"
          style={{ flex: 1 }}
          disabled={loading}
          id="chat-input"
        />
        <button 
          type="submit" 
          className="action-btn send-btn" 
          disabled={loading || !input.trim()}
          id="send-btn"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

export default App;
