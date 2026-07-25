import React, { useState } from 'react';
import { UploadCloud, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { uploadTC } from '../services/api';

const Setup = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });
  const { user } = useAuth();

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus({ type: '', message: '' });

    try {
      await uploadTC(file, user?.token || '');
      setStatus({ type: 'success', message: 'Master Terms & Conditions uploaded and processed successfully.' });
      setFile(null);
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'An error occurred' });
    } finally {
      setLoading(false);
    }
  };


  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', color: 'white' }}>Master Setup</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Upload the global Terms & Conditions document. The AI will parse this to form the baseline knowledge for all future claims.
      </p>

      <div className="glass-card" style={{ maxWidth: '600px' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Global Terms & Conditions</h3>
        
        <div 
          className="drop-zone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => document.getElementById('tc-upload').click()}
        >
          <UploadCloud size={48} color="var(--primary)" style={{ marginBottom: '1rem' }} />
          <h4>{file ? file.name : 'Click or drag document to upload'}</h4>
          <p>Supports .pdf, .docx, .txt, .json</p>
          <input 
            type="file" 
            id="tc-upload" 
            style={{ display: 'none' }} 
            onChange={(e) => setFile(e.target.files[0])}
            accept=".pdf,.docx,.txt,.json"
          />
        </div>

        {status.message && (
          <div style={{ 
            marginTop: '1.5rem', 
            padding: '1rem', 
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            background: status.type === 'success' ? 'var(--success-bg)' : 'var(--error-bg)',
            color: status.type === 'success' ? 'var(--success)' : 'var(--error)'
          }}>
            {status.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            <span>{status.message}</span>
          </div>
        )}

        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            className="btn btn-primary" 
            onClick={handleUpload} 
            disabled={!file || loading}
          >
            {loading ? (
              <>
                <Loader2 className="spinner" size={18} /> Processing...
              </>
            ) : 'Upload & Process T&C'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Setup;
