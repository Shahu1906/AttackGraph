import React from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Isolated log without polluting production console
    if (import.meta.env.DEV) {
      console.warn('ErrorBoundary caught error:', error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-6 text-center my-4 backdrop-blur-sm">
          <div className="inline-flex p-3 rounded-full bg-rose-500/10 text-rose-400 mb-3 border border-rose-500/20">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-rose-200">
            {this.props.componentName || 'Component'} Encountered an Error
          </h3>
          <p className="mt-1 text-xs text-rose-300/80 max-w-md mx-auto">
            This module suffered a temporary render failure. Other features remain fully operational.
          </p>
          <button
            onClick={this.handleReset}
            className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-rose-900/60 hover:bg-rose-800 text-rose-100 border border-rose-500/40 transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Recover Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
