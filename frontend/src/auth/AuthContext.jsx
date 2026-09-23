import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

/** Decode a JWT payload for display without verifying its signature, returning `null` if malformed. */
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

/** Provide session-backed authentication state and login/logout actions to descendants. */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    return sessionStorage.getItem('attackgraphx_token') || null;
  });

  const [user, setUser] = useState(() => {
    const savedToken = sessionStorage.getItem('attackgraphx_token');
    if (savedToken) {
      const decoded = parseJwt(savedToken);
      if (decoded) {
        return {
          username: decoded.sub || decoded.username || 'security_user',
          role: decoded.role || 'analyst',
        };
      }
    }
    return null;
  });

  const loginWithToken = (accessToken, usernameFallback = 'user') => {
    sessionStorage.setItem('attackgraphx_token', accessToken);
    setToken(accessToken);

    const decoded = parseJwt(accessToken);
    const role = decoded?.role || (usernameFallback === 'admin' ? 'admin' : 'analyst');
    const username = decoded?.sub || decoded?.username || usernameFallback;

    const userObj = { username, role };
    setUser(userObj);
    return userObj;
  };

  const logout = () => {
    sessionStorage.removeItem('attackgraphx_token');
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        role: user?.role || 'analyst',
        isAdmin,
        loginWithToken,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Return the nearest authentication context.
 *
 * @throws {Error} When called outside an `AuthProvider`.
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
