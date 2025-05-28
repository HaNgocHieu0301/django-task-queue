import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Tailwind's custom animation for in-progress icon (if not already covered by Tailwind default animate-spin)
const style = document.createElement('style');
style.textContent = `
  @keyframes spin-slow {
    to {
      transform: rotate(360deg);
    }
  }
  .animate-spin-slow {
    animation: spin-slow 3s linear infinite;
  }
  /* Custom scrollbar for TaskList (and other scrollable areas if needed) */
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: #9ca3af #e5e7eb; /* thumb (gray-400) track (gray-200) */
  }
  .scrollbar-thin::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    background: #e5e7eb; /* track (gray-200) */
    border-radius: 10px;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: #9ca3af; /* thumb (gray-400) */
    border-radius: 10px;
    border: 2px solid #e5e7eb; /* track border (gray-200) */
  }
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: #6b7280; /* thumb hover (gray-500) */
  }
`;
document.head.append(style);


const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
