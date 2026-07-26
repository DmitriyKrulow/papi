// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import api from './api/client.ts';

const token = localStorage.getItem('token');
console.log('[Main] Token from localStorage:', token ? token.substring(0, 30) + '...' : 'NONE');
console.log('[Main] localStorage keys:', Object.keys(localStorage));
console.log('[Main] localStorage.user:', localStorage.getItem('user'));
console.log('[Main] api.defaults.headers:', api.defaults.headers);
if (token) {
  console.log('[Main] ✅ Token found in localStorage, setting default header');
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  console.log('[Main] ✅ api.defaults.headers.common after set:', api.defaults.headers.common);
} else {
  console.log('[Main] ❌ No token found in localStorage');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);