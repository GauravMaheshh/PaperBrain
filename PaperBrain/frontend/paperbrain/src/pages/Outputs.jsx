import { useState, useEffect } from 'react';
import { apiOutputsList } from '../api';
import PipelineOutputs from '../components/PipelineOutputs';

export default function Outputs() {
  const [outputs, setOutputs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadOutputs();
  }, []);

  async function loadOutputs() {
    setLoading(true);
    setError('');
    try {
      const result = await apiOutputsList();
      setOutputs(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#000000',
      color: 'white',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: 'relative'
    }}>
      {/* Navigation */}
      <nav style={{
        position: 'fixed',
        top: '2rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
        padding: '0.75rem 2rem',
        backgroundColor: 'rgba(17, 24, 39, 0.8)',
        backdropFilter: 'blur(10px)',
        borderRadius: '100px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '1.25rem',
          fontWeight: 600
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          PaperBrain
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.95rem' }}>
          <a href="/" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Home</a>
          <a href="/dashboard" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Dashboard</a>
          <a href="/outputs" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Outputs</a>
          <a href="/student" style={{ color: 'white', textDecoration: 'none', opacity: 0.9 }}>Student</a>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        padding: '8rem 2rem 4rem',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <div className="page">
          <div className="page-header">
            <h1>Pipeline Outputs</h1>
            <button onClick={loadOutputs} className="btn btn-secondary" disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          
          {loading && <div className="loading">Loading outputs...</div>}
          {error && <div className="error">{error}</div>}
          {!loading && !error && <PipelineOutputs outputs={outputs} />}
        </div>
      </div>
    </div>
  );
}