import React from 'react'
import { connect } from 'react-redux'

const AccountDeleted = ({ success }) => {
    return (
        <div className="container">
            <div className="content">
                <br />
                {success.id === 204 && (
                    <h2>Your account has been deleted...</h2>
                )}
                <br />
            </div>
        </div>
    )
}

const mapStateToProps = (state) => ({
    success: state.success,
})

export default connect(mapStateToProps)(AccountDeleted)
