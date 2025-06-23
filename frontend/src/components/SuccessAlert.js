import { useState, useEffect } from 'react'
import { connect } from 'react-redux'
import '../css/Bm.css'
import { clearSuccess } from '../actions/successActions'
import PropTypes from 'prop-types'
import Alert from '@mui/material/Alert'
import AlertTitle from '@mui/material/AlertTitle'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import Collapse from '@mui/material/Collapse'
import CloseIcon from '@mui/icons-material/Close'
import { useNavigate } from 'react-router'

const SuccessAlert = ({ success, clearSuccess }) => {
    let navigate = useNavigate()
    const [open, setOpen] = useState(false)
    const [successmsg, setSuccessmsg] = useState('')

    const handleAlert = () => {
        setOpen(false)
        setSuccessmsg('')
        clearSuccess()
        if (success.id === 'SIGNUP_SUCCESS') {
            setSuccessmsg("Account created successfully, please check your email for further instructions")
            navigate('/login')
        }
        if (success.id === 204)
            setSuccessmsg('Your account is successfully deleted')
    }

    useEffect(() => {
        if (success.status) {
            setOpen(true)
            setSuccessmsg('Success message')
        }
    }, [success.id, success.msg, success.status])

    return (
        <>
            <Collapse in={open}>
                {success.id === 'SIGNUP_SUCCESS' ? (
                    <div className="alert-container" style={{}}>
                        <Alert
                            className="success-alert"
                            variant="outlined"
                            severity="success"
                            onClick={handleAlert}
                            action={
                                <Button
                                    className="alert-btn"
                                    variant="outlined"
                                    color="secondary"
                                    size="medium"
                                >
                                    Login
                                </Button>
                            }
                        >
                            <AlertTitle>Sign Up success</AlertTitle>
                            You can now login
                        </Alert>
                    </div>
                ) : (
                    <Alert
                        className="success-alert"
                        variant="filled"
                        severity="success"
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
                        {successmsg}
                    </Alert>
                )}
            </Collapse>
        </>
    )
}
const mapStateToProps = (state) => ({
    success: state.success,
})

SuccessAlert.propTypes = {
    success: PropTypes.object.isRequired,
    clearSuccess: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, { clearSuccess })(SuccessAlert)
