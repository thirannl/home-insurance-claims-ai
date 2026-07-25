import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FilePlus, Settings, LogOut, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '3rem' }}>
          <div style={{ background: 'var(--primary)', padding: '0.5rem', borderRadius: '8px' }}>
            <ShieldAlert size={24} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', color: 'white', margin: 0 }}>ClaimAI</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Accessor Portal</span>
          </div>
        </div>

        <nav style={{ flex: 1 }}>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} />
            Dashboard Overview
          </NavLink>
          <NavLink to="/assess" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <FilePlus size={20} />
            New Claim Assessment
          </NavLink>
          <div style={{ margin: '2rem 0', height: '1px', background: 'var(--border-color)' }}></div>
          <NavLink to="/setup" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Settings size={20} />
            Master Setup
          </NavLink>
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ color: 'white', fontWeight: '500' }}>{user?.name || 'Assessor'}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Logged in</div>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
