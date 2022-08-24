import { useEffect, useState } from 'react'
import { connect } from 'react-redux'
import { useNavigate } from 'react-router'
import moment from 'moment'
import '../../css/User.css'
import DelUserModal from './DelUserModal'
import ErrorAlert from '../ErrorAlert'
import { useTranslation } from 'react-i18next'
import { updateUserOptions } from '../../actions/authActions'

const User = ({ auth, err, updateUserOptions }) => {
    const { t } = useTranslation()
    const [showModal, setShowModal] = useState(false)
    const { user } = auth
    let navigate = useNavigate()

    const handleOptionsChange = () => {
        if (auth.isAuthenticated) {
            const data = {
                theme: 1,
                localization: 'et',
            }
            updateUserOptions(data)
        }
    }
    // refresh data after options update
    useEffect(() => {}, [auth?.user?.options])

    useEffect(() => {
        !auth.isAuthenticated && navigate('/')
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [auth.isAuthenticated])

    return (
        <div className="container">
            <div className="user-content">
                {err.id === 'DEL_USER_ERROR' && <ErrorAlert />}
                <ul className="user-data">
                    <h4>{t('User data')}:</h4>
                    <li>
                        {t('Name')}: {user?.first_name && user.first_name}{' '}
                        {user?.last_name && user.last_name}
                    </li>
                    <li>
                        {t('Email')}: {user?.email}
                    </li>
                    <li>
                        {t('Account created')}:{' '}
                        {moment(user?.created_at).format('lll')}
                    </li>
                    <li>
                        {t('Account updated')}:{' '}
                        {moment(user?.updated_at).format('lll')}
                    </li>
                </ul>
                <ul className="user-options">
                    <h4>{t('User options')}:</h4>
                    <li>Theme: {auth?.user?.options?.theme}</li>
                    <li>Language: {auth?.user?.options?.localization}</li>
                    <button
                        className="btn"
                        onClick={() => {
                            handleOptionsChange()
                        }}
                    >
                        {t('Save options')}
                    </button>
                </ul>
                <div className="user-delete">
                    <button
                        className="btn"
                        onClick={() => {
                            setShowModal(true)
                        }}
                    >
                        {t('Delete account')}
                    </button>
                </div>
                <DelUserModal
                    setShowModal={setShowModal}
                    showModal={showModal}
                />
            </div>
        </div>
    )
}

const mapStateToProps = (state) => ({
    auth: state.auth,
    err: state.error,
})

export default connect(mapStateToProps, { updateUserOptions })(User)
