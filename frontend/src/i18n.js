import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import Backend from 'i18next-http-backend'
import LanguageDetector from 'i18next-browser-languagedetector'

const options = {
    // order and from where user language should be detected
    order: [
        'path',
        'querystring',
        'sessionStorage',
        'cookie',
        'localStorage',
        'navigator',
        'subdomain',
        'htmlTag',
    ],
    // cache user language on
    caches: ['localStorage', 'cookie'],
}
const backendOptions = {
    loadPath: '/assets/locales/{{lng}}/translation.json',
}

i18n.use(initReactI18next) // passes i18n down to react-i18next
    .use(LanguageDetector)
    .use(Backend)
    .init({
        supportedLngs: ['en', 'et'],
        fallbackLng: 'en',
        detection: options,
        backend: backendOptions,
        debug: false,
    }
    )

export default i18n
