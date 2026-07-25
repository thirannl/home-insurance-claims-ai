import React, { useState } from 'react';
import { UploadCloud, FileText, Loader2, CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { submitClaim } from '../services/api';

const NewClaim = () => {
  const [formData, setFormData] = useState({ customerName: '', claimType: '', claimText: '' });
  const [policyFile, setPolicyFile] = useState(null);
  const [claimFile, setClaimFile] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  const { user } = useAuth();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleDrop = (e, setter) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setter(droppedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!policyFile || !formData.customerName || !formData.claimType) {
      setError('Please provide Customer Name, Claim Type, and the Policy Document.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const responseData = await submitClaim(formData, policyFile, claimFile, user?.token || '');
      setResult(responseData);
      // Store last claim_id so Dashboard can display it
      if (responseData.claim_id) {
        localStorage.setItem('last_claim_id', responseData.claim_id);
        const history = JSON.parse(localStorage.getItem('claim_history') || '[]');
        history.unshift({
          claim_id: responseData.claim_id,
          policy_id: responseData.policy_id,
          customer_name: formData.customerName,
          claim_type: formData.claimType,
          decision: responseData.assessment?.decision || 'Assessed',
          submitted_at: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
        });
        localStorage.setItem('claim_history', JSON.stringify(history.slice(0, 20)));
      }
    } catch (err) {
      setError(err.message || 'An error occurred during assessment');
    } finally {
      setLoading(false);
    }
  };


  const getStatusIcon = (status) => {
    switch (status) {
      case 'Covered': return <CheckCircle2 size={24} />;
      case 'Not Covered': return <XCircle size={24} />;
      case 'Needs Human Review': return <AlertTriangle size={24} />;
      default: return null;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'Covered': return 'status-covered';
      case 'Not Covered': return 'status-not-covered';
      case 'Needs Human Review': return 'status-review';
      default: return '';
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', color: 'white' }}>New Claim Assessment</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Upload customer policy and claim details to instantly evaluate coverage using the AI engine.</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', alignItems: 'start' }}>
        {/* Left Side: Input Form */}
        <div className="glass-card">
          <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={20} color="var(--primary)" />
            Claim Details
          </h3>

          {error && (
            <div style={{ background: 'var(--error-bg)', color: 'var(--error)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Customer Name</label>
                <input type="text" name="customerName" className="input-field" value={formData.customerName} onChange={handleInputChange} placeholder="e.g. John Doe" required />
              </div>
              <div className="input-group">
                <label className="input-label">Claim Type</label>
                <input type="text" name="claimType" className="input-field" value={formData.claimType} onChange={handleInputChange} placeholder="e.g. Flood, Fire" required />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Policy Document (Required)</label>
              <div 
                className={`drop-zone ${policyFile ? 'active' : ''}`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => handleDrop(e, setPolicyFile)}
                onClick={() => document.getElementById('policy-upload').click()}
                style={{ padding: '1.5rem' }}
              >
                <UploadCloud size={32} color={policyFile ? "var(--primary)" : "var(--text-muted)"} style={{ marginBottom: '0.5rem' }} />
                <h5 style={{ color: policyFile ? 'white' : 'inherit' }}>{policyFile ? policyFile.name : 'Upload Policy File'}</h5>
                <input type="file" id="policy-upload" style={{ display: 'none' }} onChange={(e) => setPolicyFile(e.target.files[0])} />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Claim Document (Optional)</label>
              <div 
                className={`drop-zone ${claimFile ? 'active' : ''}`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => handleDrop(e, setClaimFile)}
                onClick={() => document.getElementById('claim-upload').click()}
                style={{ padding: '1.5rem' }}
              >
                <UploadCloud size={32} color={claimFile ? "var(--primary)" : "var(--text-muted)"} style={{ marginBottom: '0.5rem' }} />
                <h5 style={{ color: claimFile ? 'white' : 'inherit' }}>{claimFile ? claimFile.name : 'Upload Claim Document'}</h5>
                <input type="file" id="claim-upload" style={{ display: 'none' }} onChange={(e) => setClaimFile(e.target.files[0])} />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Or Type Claim Statement</label>
              <textarea 
                name="claimText" 
                className="input-field" 
                rows="4" 
                value={formData.claimText} 
                onChange={handleInputChange} 
                placeholder="Describe the claim details..."
                style={{ resize: 'vertical' }}
              ></textarea>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="spinner" size={18} /> Analyzing Documents...
                </>
              ) : 'Evaluate Claim'}
            </button>
          </form>
        </div>

        {/* Right Side: AI Output */}
        <div className="glass-card" style={{ minHeight: '500px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Info size={20} color="var(--primary)" />
            AI Assessment Report
          </h3>

          {!loading && !result && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '50%', marginBottom: '1rem' }}>
                <FileText size={48} opacity={0.5} />
              </div>
              <p>Submit a claim to view the AI assessment results here.</p>
            </div>
          )}

          {loading && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
              <Loader2 className="spinner" size={48} style={{ marginBottom: '1rem', borderTopColor: 'var(--primary)' }} />
              <p style={{ fontWeight: '500', animation: 'pulse 2s infinite' }}>Analyzing documents and querying FAISS...</p>
            </div>
          )}

          {result && !loading && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <div style={{ marginBottom: '2rem' }}>
                <span className="input-label">Decision</span>
                <div className={`status-badge ${getStatusClass(result.assessment.decision)}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', padding: '0.5rem 1rem', marginTop: '0.5rem' }}>
                  {getStatusIcon(result.assessment.decision)}
                  {result.assessment.decision}
                </div>
              </div>

              <div style={{ marginBottom: '2rem' }}>
                <span className="input-label">Justification</span>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '1.25rem', borderRadius: '12px', lineHeight: '1.6', color: 'white', border: '1px solid var(--border-color)' }}>
                  {result.assessment.justification}
                </div>
              </div>

              {result.assessment.flags && result.assessment.flags.length > 0 && (
                <div>
                  <span className="input-label">Flags & Alerts</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                    {result.assessment.flags.map((flag, index) => (
                      <span key={index} className="chip" style={{ background: 'var(--warning-bg)', color: 'var(--warning)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                        <AlertTriangle size={14} style={{ marginRight: '0.375rem' }} />
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                <span>Claim ID: #{result.claim_id}</span>
                <span>Policy ID: #{result.policy_id}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewClaim;
