import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location, message: 'Session expired or authentication required.' }} replace />;
  }

  if (adminOnly && !isAdmin) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-rose-500/30 p-8 rounded-xl max-w-md text-center shadow-2xl">
          <h2 className="text-xl font-bold text-rose-400">Access Denied</h2>
          <p className="mt-2 text-sm text-slate-300">
            Administrative access required to perform this action.
          </p>
          <a
            href="/"
            className="mt-6 inline-block px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors"
          >
            Return to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return children;
}
