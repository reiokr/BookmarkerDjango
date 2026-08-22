import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import {
  FiBookmark,
  FiYoutube,
  FiFolder,
  FiLayers,
  FiArrowRight,
  FiCheckCircle,
  FiGithub,
} from 'react-icons/fi';
import { applyThemeToDocument } from '../utils/themeUtils';

const THEMES = [
  { id: '0', name: 'Nocturne', gradient: 'linear-gradient(135deg, #f0a030, #d4891a)' },
  { id: '1', name: 'Ocean', gradient: 'linear-gradient(135deg, #38bdf8, #0ea5e9)' },
  { id: '2', name: 'Violet', gradient: 'linear-gradient(135deg, #a78bfa, #8b5cf6)' },
  { id: '3', name: 'Light', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { id: '4', name: 'Aurora', gradient: 'linear-gradient(135deg, #34d399, #22d3ee, #f472b6)' },
];

const Landing = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTheme, setActiveTheme] = useState(
    () => document.documentElement.getAttribute('data-theme') || '0',
  );

  // Restore the user's saved theme when leaving the landing showcase
  useEffect(() => {
    return () => {
      const stored = localStorage.getItem('theme');
      if (stored) applyThemeToDocument(stored);
    };
  }, []);

  const handleThemePreview = (id) => {
    applyThemeToDocument(id);
    setActiveTheme(id);
  };

  const features = [
    {
      icon: <FiBookmark />,
      title: t('landing_feature_save_title'),
      desc: t('landing_feature_save_desc'),
    },
    {
      icon: <FiYoutube />,
      title: t('landing_feature_yt_title'),
      desc: t('landing_feature_yt_desc'),
    },
    {
      icon: <FiFolder />,
      title: t('landing_feature_cats_title'),
      desc: t('landing_feature_cats_desc'),
    },
    {
      icon: <FiLayers />,
      title: t('landing_feature_themes_title'),
      desc: t('landing_feature_themes_desc'),
    },
  ];

  return (
    <div className="landing">
      <div className="landing-aurora" aria-hidden="true" />

      {/* Hero */}
      <section className="landing-hero">
        <span className="landing-hero-badge landing-reveal landing-reveal-1">
          <span className="landing-badge-dot" />
          {t('landing_hero_badge')}
        </span>

        <h1 className="landing-hero-title landing-reveal landing-reveal-2">
          {t('landing_hero_title')}
        </h1>

        <p className="landing-hero-subtitle landing-reveal landing-reveal-3">
          {t('landing_hero_subtitle')}
        </p>

        <div className="landing-hero-cta landing-reveal landing-reveal-4">
          <button
            type="button"
            className="landing-btn landing-btn--primary"
            onClick={() => navigate('/signup')}
          >
            {t('landing_signup_cta')}
            <FiArrowRight />
          </button>
          <Link to="/login" className="landing-btn landing-btn--ghost">
            {t('landing_login_cta')}
          </Link>
        </div>

        <div className="landing-hero-meta landing-reveal landing-reveal-5">
          <span>
            <FiCheckCircle />
            {t('landing_meta_free')}
          </span>
          <span>
            <FiCheckCircle />
            {t('landing_meta_no_card')}
          </span>
          <span>
            <FiCheckCircle />
            {t('landing_meta_open_source')}
          </span>
        </div>
      </section>

      {/* Features */}
      <section className="landing-features">
        <div className="landing-section-head">
          <h2>{t('landing_features_title')}</h2>
          <p>{t('landing_features_subtitle')}</p>
        </div>
        <div className="landing-feature-grid">
          {features.map((f, i) => (
            <div
              key={f.title}
              className={`landing-feature-card landing-reveal landing-reveal-${(i % 4) + 1}`}
            >
              <div className="landing-feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Theme showcase */}
      <section className="landing-themes">
        <div className="landing-section-head">
          <h2>{t('landing_theme_showcase_title')}</h2>
          <p>{t('landing_theme_showcase_desc')}</p>
        </div>
        <div className="landing-theme-grid">
          {THEMES.map((theme) => (
            <button
              key={theme.id}
              type="button"
              className={`landing-theme-card${activeTheme === theme.id ? ' is-active' : ''}`}
              onClick={() => handleThemePreview(theme.id)}
              aria-pressed={activeTheme === theme.id}
            >
              <span className="landing-theme-active-tag">Live</span>
              <span
                className="landing-theme-swatch"
                style={{ background: theme.gradient }}
              />
              <span className="landing-theme-name">{theme.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <span>
          {t('landing_footer_made_with')} <span className="landing-footer-heart">♥</span>{' '}
          · © {new Date().getFullYear()} Bookmarker
        </span>
        <a
          href="https://github.com/reiokr/BookmarkerDjango"
          target="_blank"
          rel="noreferrer"
        >
          <FiGithub style={{ marginRight: 6, verticalAlign: 'middle' }} />
          GitHub
        </a>
      </footer>
    </div>
  );
};

export default Landing;
