import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './i18n';
import './index.css';
import App from './App';

// Roadmap step [2.2]: the refresh token is an HttpOnly cookie scoped to
// /api/login/. Every API request must be eligible to carry it, so the
// shared client is configured ONCE here instead of per call site.
// (Same-origin through the CRA dev proxy already sends cookies; this
// also covers cross-origin deployments.)
axios.defaults.withCredentials = true;

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
