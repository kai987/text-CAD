import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { LanguageProvider } from './LanguageContext';
import { ThemeProvider } from './ThemeContext';
import './styles.css';

createRoot(document.getElementById('root')!).render(<StrictMode><LanguageProvider><ThemeProvider><App /></ThemeProvider></LanguageProvider></StrictMode>);
