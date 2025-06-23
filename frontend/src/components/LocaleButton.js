import { useEffect } from 'react'
import i18next from 'i18next'
import TranslateOutlinedIcon from '@mui/icons-material/TranslateOutlined'
import { useTranslation } from 'react-i18next'
import { languages } from './lang'

const LocaleButton = () => {
    const currentLanguageCode = localStorage.getItem('i18nextLng') || 'en'
    const currentLanguage = languages.find(
        (l) => l.code === currentLanguageCode
    )
    const { t } = useTranslation()
    useEffect(() => {
        // console.log('Setting page stuff');
        document.body.dir = currentLanguage.dir || 'ltr'
        document.title = t('app_title')
    }, [currentLanguage, t])

    useEffect(() => {
        // window.location = window.location + currentLanguage.code
    }, [currentLanguage.code])
    return (
        <div className="dropdown">
            <button className="dropbtn">
                <TranslateOutlinedIcon />
            </button>
            <div className="dropdown-content">
                {languages.map(({ code, name, country_code }) => (
                    <div
                        key={country_code}
                        onClick={() => {
                            i18next.changeLanguage(code)
                        }}
                    >
                        <span
                            className={`flag-icon flag-icon-${country_code} mx-2`}
                            style={{
                                opacity: currentLanguageCode === code ? 0.5 : 1,
                            }}
                        ></span>
                        {name}
                    </div>
                ))}
            </div>
        </div>
    )
}

export default LocaleButton
