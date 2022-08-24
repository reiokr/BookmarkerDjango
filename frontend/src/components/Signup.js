import { useEffect } from 'react'
import { connect } from 'react-redux'
import '../css/signup.css'
import { useNavigate } from 'react-router'
import { signUpUser } from '../actions/authActions'
import ErrorAlert from './ErrorAlert'
import { clearErrors } from '../actions/errorActions'
import { clearSuccess } from '../actions/successActions'
import {useTranslation} from 'react-i18next'

const Signup = ({ signUpUser, auth, success, err }) => {
    let navigate = useNavigate()
    const {t} = useTranslation()
    const handleSubmit = (e) => {
        e.preventDefault()
        const data = new FormData(e.currentTarget)
        // data.append('username', data.get('username'))
        data.append('email', data.get('email'))
        data.append('password', data.get('password'))
        data.append('password2', data.get('password2'))

        signUpUser(data)
    }

    useEffect(() => {
        if (auth.isAuthenticated) navigate('/login')
    }, [auth.isAuthenticated, navigate])
// console.log(err)
    return (
        <>
            <div className="signup-form-container">
                {/* <SuccessAlert /> */}
                <h1>{t('Sign Up')}</h1>
                <form onSubmit={handleSubmit}>
                    {/* <input
                        autoComplete="off"
                        type="text"
                        name="username"
                        id="username"
                        placeholder="Username"
                      /> */}
                      {err.id === 'SIGNUP_ERROR' && err.msg.email&& <ErrorAlert />}
                    <input
                        autoComplete="off"
                        type="email"
                        name="email"
                        id="email"
                        placeholder={t('Email')}
                        required
                        />
                        {err.id === 'SIGNUP_ERROR' && err.msg.password &&<ErrorAlert />}
                    <input
                        type="password"
                        name="password"
                        id="password"
                        placeholder={t("Password")}
                        required
                        />
                        {err.id === 'SIGNUP_ERROR' && err.msg.password2 && <ErrorAlert />}
                    <input
                        type="password"
                        name="password2"
                        id="password2"
                        placeholder={t('Password again')}
                        required
                    />
                    <div className="form-buttons">
                        <input
                            type="submit"
                            name="submit"
                            id="submit"
                            value={t('signup_btn')}
                        />
                    </div>
                </form>
            </div>
        </>
    )
}
const mapStateToProps = (state) => ({
    auth: state.auth,
    success: state.success,
    err: state.error,
})
export default connect(mapStateToProps, {
    signUpUser,
    clearErrors,
    clearSuccess,
})(Signup)
