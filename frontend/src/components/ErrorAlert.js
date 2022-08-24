import { useState, useEffect } from 'react'
import { connect } from 'react-redux'
import '../css/Bm.css'
import { clearErrors } from '../actions/errorActions'
import PropTypes from 'prop-types'
import Alert from '@mui/material/Alert'
import IconButton from '@mui/material/IconButton'
import Collapse from '@mui/material/Collapse'
import CloseIcon from '@mui/icons-material/Close'
import { useTranslation } from 'react-i18next'

const ErrorAlert = ({ err, clearErrors, data }) => {
    const [open, setOpen] = useState(false)
    const [errmsg, setErrmsg] = useState('')
    const { t } = useTranslation()
    const handleAlert = () => {
        setOpen(false)
        setTimeout(() => {
            setErrmsg('')
            clearErrors()
        }, 200)
    }


    useEffect(() => {
      // console.log(err);
        if (err.status) {
            setOpen(true)
            if (err.status === 500) setErrmsg(t('Server error'))
            if (err.status === 504) setErrmsg(err.msg.detail)
            if (err.status === 422) setErrmsg(err.msg.detail)
            if (err.id === 'ADD_BM_ERROR') setErrmsg(t("Url error"))
            if (err.id === 'GET_BM_ERROR') setErrmsg(t('No bookmarks found'))
            // if (err.id === 'LOGIN_ERROR') setErrmsg(t('Incorrect email or password'))
            if (err.id === 'LOGIN_ERROR') setErrmsg(t(err.msg.detail))
            if (err.id === 'CATEGORY_ERROR') setErrmsg(t('Category already exists'))
            if (err.id === 'DEL_CATEGORY_ERROR') setErrmsg(err.msg.detail)
            if (err.id === 'SIGNUP_ERROR' && err.msg.email)
                setErrmsg(err.msg.email[0]);
            if (err.id === 'SIGNUP_ERROR' && err.msg.password)
                setErrmsg(err.msg.password[0]);
            if (err.id === 'SIGNUP_ERROR' && err.msg.password2)
                setErrmsg(err.msg.password2[0]);
            if (err.id === 'FILTER_ERROR') setErrmsg(err.msg.detail)
            if (err.id === 'CATEGORY_NAME_ERROR') setErrmsg(t('Category name required'))
            if (err.id === 'VERIFY_EMAIL_ERROR') setErrmsg(t('Please provide correct email'))
            if (err.id === 'DEL_USER_ERROR') setErrmsg(err.msg.detail)
            if (err.id === 'LOGIN_FAIL') setErrmsg(err.msg)
            if (err.id === 'USER_NOT_ACTIVE') setErrmsg(err.msg)
            if(err.id ==='RELATED_VIDEOS_ERROR') setErrmsg(err.msg)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data.bm, err.id, err.msg, err.status])

    // console.log(err);

    return (
        <>
            <Collapse in={open}>
                <Alert
                    className="error-alert"
                    variant="filled"
                    severity="error"
                    action={
                        <IconButton
                            aria-label="close"
                            color="inherit"
                            size="small"
                            onClick={handleAlert}
                        >
                            <CloseIcon fontSize="inherit" />
                        </IconButton>
                    }
                >
                    {errmsg}
                </Alert>
            </Collapse>
        </>
    )
}
const mapStateToProps = (state) => ({
    err: state.error,
    data: state.bm,
})

ErrorAlert.propTypes = {
    err: PropTypes.object.isRequired,
    clearErrors: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, { clearErrors })(ErrorAlert)
