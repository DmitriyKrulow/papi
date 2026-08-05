// frontend/src/main.tsx
import './utils/global-fetch-handler'; // Глобальный обработчик 401 ошибок
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);