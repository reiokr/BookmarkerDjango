import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import './i18n';
import './index.css';
import App from './App';

const loadingMarkup = (
    <div>
        <p>...</p>
    </div>
);

const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);

root.render(
    <React.StrictMode>
        <Suspense fallback={loadingMarkup}>
            <App />
        </Suspense>
    </React.StrictMode>
);
