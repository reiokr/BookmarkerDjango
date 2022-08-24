import '../css/Login.css'
import { connect } from 'react-redux'
import PropTypes from 'prop-types'
import { loginUser } from '../actions/authActions'
import { Link } from 'react-router-dom'
import { Navigate } from 'react-router-dom'
import ErrorAlert from './ErrorAlert'
import SuccessAlert from './SuccessAlert'
import {useTranslation} from 'react-i18next'

const Login = ({ auth, err,success, loginUser }) => {
  const {t} = useTranslation()
    const handleSubmit = (e) => {
        e.preventDefault()
        const data = new FormData(e.currentTarget)
        data.append('email', data.get('email'))
        data.append('password', data.get('password'))
        loginUser(data)
    }
// console.log(err)
    return (
        <div className="login-form">
            {err.id === 'LOGIN_ERROR' && <ErrorAlert />}
            {err.id === 'LOGIN_FAIL' && <ErrorAlert />}
            {err.id === 'USER_NOT_ACTIVE' && <ErrorAlert />}
            {success.id === 'SIGNUP_SUCCESS' && <SuccessAlert />}
            {auth.isAuthenticated && <Navigate to="/" />}
            <h1>{t('log in')}</h1>
            <form onSubmit={handleSubmit}>
                <input
                    required
                    type="email"
                    name="email"
                    placeholder="Email..."
                    autoComplete="email"
                    id="email"
                    autoFocus
                />
                <input
                    required
                    type="password"
                    name="password"
                    placeholder="Password..."
                    autoComplete="current-password"
                    id="password"
                />
                <div className="rememberme">
                    <input
                        className="check-rememberme"
                        type="checkbox"
                        name="remember"
                        id="rememberme"
                    />
                    <label htmlFor="rememberme">{t('remember_me')}</label>
                </div>
                <button type="submit">{t('login_btn')}</button>
                <Link className="ref-btn" to="/restorepwd">
                    {t('Forgot your password?')}
                </Link>
                <Link className="ref-btn" to="/signup">
                    {t('Not registered?')}
                </Link>
            </form>
        </div>
    )
}

const mapStateToProps = (state) => ({
    auth: state.auth,
    err: state.error,
    success: state.success,
})

Login.porpTypes = {
    auth: PropTypes.object.isRequired,
    err: PropTypes.object.isRequired,
    loginUser: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, { loginUser })(Login)
