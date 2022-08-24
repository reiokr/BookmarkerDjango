import React from 'react'
import { useTranslation } from 'react-i18next'

const Logout = () => {
    const { t } = useTranslation()
    return (
        <div className="container">
            <div className="info-text">
                <p>{t('You are now logged out')}</p>
                <p>
                    {t(
                        'You can now log in again or register a new account or go to'
                    )}{' '}
                    <a className="ref-btn" href="/">
                        {t('HomePage')}
                    </a>
                </p>
            </div>
        </div>
    )
}

export default Logout
