import React, { useState, useEffect } from 'react';
import { ShieldCheck, Clock, CheckCircle2, XCircle, AlertTriangle, FileSearch, ChevronRight, Loader2, UserCheck, UserX } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getClaimStatus, overrideClaimDecision, getAllClaims } from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [recentClaims, setRecentClaims] = useState([]);
  const [claimsLoading, setClaimsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [claimDetails, setClaimDetails] = useState({});
  const [loadingDetails, setLoadingDetails] = useState({});
  const [overrideLoading, setOverrideLoading] = useState({});

  const toggleRow = async (claimId) => {
    if (expandedId === claimId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(claimId);
    
    if (!claimDetails[claimId]) {
      setLoadingDetails(prev => ({ ...prev, [claimId]: true }));
      try {
        const data = await getClaimStatus(claimId, user?.token);
        setClaimDetails(prev => ({ ...prev, [claimId]: data }));
      } catch (err) {
        console.error("Failed to fetch claim details", err);
      } finally {
        setLoadingDetails(prev => ({ ...prev, [claimId]: false }));
      }
    }
  };

  const handleOverride = async (claimId, decision) => {
    setOverrideLoading(prev => ({ ...prev, [claimId]: true }));
    try {
      await overrideClaimDecision(claimId, decision, user?.token);
      // Optimistic update — reflect change immediately without a page reload
      setRecentClaims(prev => prev.map(c =>
        c.claim_id === claimId ? { ...c, final_decision: decision, reviewed_by: user?.name } : c
      ));
      setClaimDetails(prev => ({
        ...prev,
        [claimId]: { ...prev[claimId], final_decision: decision, reviewed_by: user?.name }
      }));
    } catch (err) {
      console.error('Override failed', err);
      alert('Failed to override: ' + err.message);
    } finally {
      setOverrideLoading(prev => ({ ...prev, [claimId]: false }));
    }
  };

  // Load all claims live from the DB (not localStorage) so final_decision is always current
  useEffect(() => {
    if (!user?.token) return;
    setClaimsLoading(true);
    getAllClaims(user.token)
      .then(data => setRecentClaims(data.claims || []))
      .catch(err => console.error('Failed to load claims', err))
      .finally(() => setClaimsLoading(false));
  }, [user]);

  // Use final_decision when present, else fall back to AI decision
  const effectiveDecision = (c) => c.final_decision || c.decision;

  const stats = {
    // AI approved — no human override, AI said Covered
    aiApproved:       recentClaims.filter(c => !c.final_decision && c.decision === 'Covered').length,
    // Human reviewed and approved
    reviewedApproved: recentClaims.filter(c => c.final_decision === 'Covered').length,
    // Denied — effective decision is Not Covered (AI or human)
    denied:           recentClaims.filter(c => effectiveDecision(c) === 'Not Covered' && !c.final_decision).length,
    // Human reviewed and denied
    reviewedDenied:   recentClaims.filter(c => c.final_decision === 'Not Covered').length,
    // Still awaiting human review (AI flagged, not yet overridden)
    review:           recentClaims.filter(c => !c.final_decision && c.decision === 'Needs Human Review').length,
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

      {/* ── 5-column stats grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>

        {/* AI Approved */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem' }}>
          <div style={{ background: 'var(--success-bg)', padding: '0.875rem', borderRadius: '12px', flexShrink: 0 }}>
            <ShieldCheck size={24} color="var(--success)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '500', lineHeight: 1.3 }}>AI Approved</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.2rem' }}>{stats.aiApproved}</div>
          </div>
        </div>

        {/* Reviewed & Approved */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem', outline: '1px solid rgba(16,185,129,0.2)' }}>
          <div style={{ background: 'rgba(16,185,129,0.15)', padding: '0.875rem', borderRadius: '12px', flexShrink: 0 }}>
            <UserCheck size={24} color="var(--success)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '500', lineHeight: 1.3 }}>Reviewed &amp; Approved</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success)', marginTop: '0.2rem' }}>{stats.reviewedApproved}</div>
          </div>
        </div>

        {/* AI Denied */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem' }}>
          <div style={{ background: 'var(--error-bg)', padding: '0.875rem', borderRadius: '12px', flexShrink: 0 }}>
            <XCircle size={24} color="var(--error)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '500', lineHeight: 1.3 }}>AI Denied</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.2rem' }}>{stats.denied}</div>
          </div>
        </div>

        {/* Reviewed & Denied */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem', outline: '1px solid rgba(239,68,68,0.2)' }}>
          <div style={{ background: 'rgba(239,68,68,0.15)', padding: '0.875rem', borderRadius: '12px', flexShrink: 0 }}>
            <UserX size={24} color="var(--error)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '500', lineHeight: 1.3 }}>Reviewed &amp; Denied</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--error)', marginTop: '0.2rem' }}>{stats.reviewedDenied}</div>
          </div>
        </div>

        {/* Pending Review */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem' }}>
          <div style={{ background: 'var(--warning-bg)', padding: '0.875rem', borderRadius: '12px', flexShrink: 0 }}>
            <Clock size={24} color="var(--warning)" />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: '500', lineHeight: 1.3 }}>Pending Review</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'white', marginTop: '0.2rem' }}>{stats.review}</div>
          </div>
        </div>

      </div>

      <div className="glass-card">
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem' }}>Recent Assessments</h3>

        {claimsLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '3rem', color: 'var(--text-muted)', justifyContent: 'center' }}>
            <Loader2 size={20} className="spinner" /> Loading claims...
          </div>
        ) : recentClaims.length === 0 ? (
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
                  <th style={{ padding: '1rem', fontWeight: '500' }}>Decision</th>
                </tr>
              </thead>
              <tbody>
                {recentClaims.map((claim) => (
                  <React.Fragment key={claim.claim_id}>
                    <tr 
                      onClick={() => toggleRow(claim.claim_id)}
                      style={{ 
                        borderBottom: '1px solid rgba(255,255,255,0.05)', 
                        cursor: 'pointer',
                        transition: 'background 0.2s',
                        background: expandedId === claim.claim_id ? 'rgba(255,255,255,0.03)' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '1rem', color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <ChevronRight 
                          size={16} 
                          style={{ 
                            transition: 'transform 0.2s', 
                            transform: expandedId === claim.claim_id ? 'rotate(90deg)' : 'rotate(0deg)',
                            color: 'var(--text-muted)'
                          }} 
                        />
                        #{claim.claim_id}
                      </td>
                      <td style={{ padding: '1rem', color: 'white' }}>{claim.customer_name}</td>
                      <td style={{ padding: '1rem' }}>{claim.claim_type}</td>
                      <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{claim.submitted_at}</td>
                      <td style={{ padding: '1rem' }}>
                        {claim.final_decision ? (
                          <span
                            className={`status-badge ${getStatusClass(claim.final_decision)}`}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', border: '1px solid var(--primary)' }}
                          >
                            {getStatusIcon(claim.final_decision)}
                            Reviewed: {claim.final_decision}
                          </span>
                        ) : (
                          <span className={`status-badge ${getStatusClass(claim.decision)}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
                            {getStatusIcon(claim.decision)}
                            {claim.decision}
                          </span>
                        )}
                      </td>
                    </tr>
                    {expandedId === claim.claim_id && (
                      <tr style={{ background: 'rgba(15, 23, 42, 0.4)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td colSpan="5" style={{ padding: '1.5rem' }}>
                          {loadingDetails[claim.claim_id] ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                              <Loader2 size={16} className="spinner" /> Loading claim details...
                            </div>
                          ) : claimDetails[claim.claim_id] ? (
                            <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                                <div>
                                  <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Justification</h4>
                                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', color: 'white', fontSize: '0.9rem', lineHeight: '1.5', border: '1px solid rgba(255,255,255,0.05)' }}>
                                    {claimDetails[claim.claim_id].justification || claimDetails[claim.claim_id].assessment?.justification || 'No justification available.'}
                                  </div>
                                </div>
                                <div>
                                  <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Flags & Alerts</h4>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {(claimDetails[claim.claim_id].flags || claimDetails[claim.claim_id].assessment?.flags)?.length > 0 ? (
                                      (claimDetails[claim.claim_id].flags || claimDetails[claim.claim_id].assessment.flags).map((flag, idx) => (
                                        <span key={idx} className="chip" style={{ background: 'var(--warning-bg)', color: 'var(--warning)', border: '1px solid rgba(245, 158, 11, 0.2)', fontSize: '0.8rem', padding: '0.25rem 0.5rem', display: 'inline-flex', alignItems: 'center' }}>
                                          <AlertTriangle size={12} style={{ marginRight: '0.25rem' }} />
                                          {flag}
                                        </span>
                                      ))
                                    ) : (
                                      <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No flags</span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* ── Human Override Section ── */}
                              <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                  Human Override
                                </h4>
                                {claimDetails[claim.claim_id].final_decision ? (
                                  <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', background: 'rgba(0,0,0,0.2)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                    Decision overridden to{' '}
                                    <strong style={{ color: 'white' }}>{claimDetails[claim.claim_id].final_decision}</strong>
                                    {' '}by <strong style={{ color: 'white' }}>{claimDetails[claim.claim_id].reviewed_by || 'an assessor'}</strong>.
                                  </div>
                                ) : (
                                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                                    <button
                                      id={`approve-${claim.claim_id}`}
                                      onClick={() => handleOverride(claim.claim_id, 'Covered')}
                                      disabled={overrideLoading[claim.claim_id]}
                                      className="btn"
                                      style={{ background: 'var(--success-bg)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.2)', cursor: overrideLoading[claim.claim_id] ? 'not-allowed' : 'pointer', opacity: overrideLoading[claim.claim_id] ? 0.6 : 1 }}
                                    >
                                      {overrideLoading[claim.claim_id] ? 'Saving...' : '✓ Approve Claim'}
                                    </button>
                                    <button
                                      id={`reject-${claim.claim_id}`}
                                      onClick={() => handleOverride(claim.claim_id, 'Not Covered')}
                                      disabled={overrideLoading[claim.claim_id]}
                                      className="btn"
                                      style={{ background: 'var(--error-bg)', color: 'var(--error)', border: '1px solid rgba(239, 68, 68, 0.2)', cursor: overrideLoading[claim.claim_id] ? 'not-allowed' : 'pointer', opacity: overrideLoading[claim.claim_id] ? 0.6 : 1 }}
                                    >
                                      {overrideLoading[claim.claim_id] ? 'Saving...' : '✕ Reject Claim'}
                                    </button>
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div style={{ color: 'var(--error)' }}>Failed to load details.</div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
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

