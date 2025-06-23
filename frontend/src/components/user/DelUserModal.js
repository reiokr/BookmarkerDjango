import { useState, useEffect } from 'react'
import { connect } from 'react-redux'
import { deleteUser, logout } from '../../actions/authActions'
import { returnErrors, clearErrors } from '../../actions/errorActions'
import ErrorAlert from '../ErrorAlert'
import { useNavigate } from 'react-router'
import LdsFacebook from '../LdsFacebook'
import {useTranslation} from 'react-i18next'

const DelUserModal = ({
    auth,
    setShowModal,
    showModal,
    deleteUser,
    logout,
    success,
    err,
    returnErrors,
    clearErrors,
}) => {
    const [email, setEmail] = useState('')
    const [isTrue, setIsTrue] = useState(false)
    const navigate = useNavigate()
    const {t} = useTranslation()

    const handleDeleteAccount = () => {
        if (email === auth.user.email) {
            setIsTrue(true)
            deleteUser(auth.user.id)
            logOut()
        } else {
            returnErrors({ msg: t("Wrong email") }, 400, 'VERIFY_EMAIL_ERROR')
        }
    }
    const handleChange = (e) => {
        setEmail(e.target.value)
    }

    // console.log(success)
    const logOut = () => {
        if (success.id === 200) {
            logout()
            navigate('/user/deleted')
            clearErrors()
        }
        setIsTrue(false)
        setShowModal(false)
    }

    useEffect(() => {
        if (!auth.isAuthenticated) navigate('/')
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [auth.isAuthenticated])

    return (
        <div
            className={`${
                showModal
                    ? 'show-delete-account-modal user-delete-modal'
                    : 'user-delete-modal'
            }`}
        >
            <p>{t("Are you sure you want to delete your account?")}</p>
            <p>{t("All account data and bookmarks will be deleted.")}</p>
            {isTrue && (
                <div className="delete-user-loader">
                    <LdsFacebook />
                </div>
            )}
            <div className="user-modal-buttons">
                <input
                    onChange={handleChange}
                    name="text"
                    id="text"
                    type="text"
                    placeholder={t("please type your email")}
                    autoComplete="off"
                />

                <button className="btn" onClick={handleDeleteAccount}>
                    {t("Yes")}
                </button>
                <button
                    className="btn"
                    onClick={() => {
                        setShowModal(false)
                        clearErrors()
                    }}
                >
                    {t("No")}
                </button>
            </div>
            {err.id === 'VERIFY_EMAIL_ERROR' && (
                <>
                    <br />
                    <ErrorAlert />
                </>
            )}
        </div>
    )
}

const mapStateToProps = (state) => ({
    auth: state.auth,
    err: state.error,
    success: state.success,
})

export default connect(mapStateToProps, {
    deleteUser,
    logout,
    returnErrors,
    clearErrors,
})(DelUserModal)
