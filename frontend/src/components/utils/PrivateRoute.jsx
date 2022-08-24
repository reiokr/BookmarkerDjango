import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { connect } from 'react-redux'

const PrivateRoute = ({ auth, children, ...rest }) => {
    return auth.isAuthenticated ? (
        <Outlet {...rest}>{children}</Outlet>
    ) : (
        <Navigate to="/login" />
    )
}

const mapStateToProps = (state) => ({
    auth: state.auth,
})

export default connect(mapStateToProps)(PrivateRoute)
