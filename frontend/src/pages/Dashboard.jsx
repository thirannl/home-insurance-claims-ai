import React, { useState, useEffect } from 'react';
import { ShieldCheck, Clock, CheckCircle2, XCircle, AlertTriangle, FileSearch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();
  const [recentClaims, setRecentClaims] = useState([]);

  useEffect(() => {
    const history = JSON.parse(localStorage.getItem('claim_history') || '[]');
    setRecentClaims(history);
  }, []);

  const stats = {
    covered: recentClaims.filter(c => c.decision === 'Covered').length,
    notCovered: recentClaims.filter(c => c.decision === 'Not Covered').length,
    review: recentClaims.filter(c => c.decision === 'Needs Human Review').length,
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Covered': return <CheckCircle2 size={16} />;
      case 'Not Covered': return <XCircle size={16} />;
      case 'Needs Human Review': return <AlertTriangle size={16} />;
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ color: 'white', marginBottom: '0.25rem' }}>Dashboard Overview</h2>
          <p style={{ color: 'var(--text-muted)' }}>Welcome back! Here's a summary of recent AI claim assessments.</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/assess')}>
          + New Assessment
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'var(--success-bg)', padding: '1rem', borderRadius: '12px' }}>
            <ShieldCheck size={28} color="var(--success)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: '500' }}>Approved Claims</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.25rem' }}>{stats.covered}</div>
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'var(--error-bg)', padding: '1rem', borderRadius: '12px' }}>
            <XCircle size={28} color="var(--error)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: '500' }}>Denied Claims</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.25rem' }}>{stats.notCovered}</div>
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'var(--warning-bg)', padding: '1rem', borderRadius: '12px' }}>
            <Clock size={28} color="var(--warning)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: '500' }}>Pending Review</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.25rem' }}>{stats.review}</div>
          </div>
        </div>
      </div>

      <div className="glass-card">
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem' }}>Recent Assessments</h3>

        {recentClaims.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <FileSearch size={48} style={{ marginBottom: '1rem', opacity: 0.4 }} />
            <p>No assessments yet. <button className="btn btn-primary" style={{ marginLeft: '0.5rem', padding: '0.4rem 1rem', fontSize: '0.875rem' }} onClick={() => navigate('/assess')}>Submit your first claim →</button></p>
          </div>
        ) : (
          <div style={{ width: '100%', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '1rem', fontWeight: '500' }}>Claim ID</th>
                  <th style={{ padding: '1rem', fontWeight: '500' }}>Customer</th>
                  <th style={{ padding: '1rem', fontWeight: '500' }}>Type</th>
                  <th style={{ padding: '1rem', fontWeight: '500' }}>Date</th>
                  <th style={{ padding: '1rem', fontWeight: '500' }}>AI Decision</th>
                </tr>
              </thead>
              <tbody>
                {recentClaims.map((claim) => (
                  <tr key={claim.claim_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '1rem', color: 'white' }}>#{claim.claim_id}</td>
                    <td style={{ padding: '1rem', color: 'white' }}>{claim.customer_name}</td>
                    <td style={{ padding: '1rem' }}>{claim.claim_type}</td>
                    <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{claim.submitted_at}</td>
                    <td style={{ padding: '1rem' }}>
                      <span className={`status-badge ${getStatusClass(claim.decision)}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
                        {getStatusIcon(claim.decision)}
                        {claim.decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

