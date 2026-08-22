import React from 'react'

// Shown when the account was created but the activation email could not
// be delivered (backend reports email_sent=false on POST /api/register/).
const EmailError = () => {
  return (
    <div className="email-error-note" role="alert">
      Your account was created, but the activation email could not be sent.
      Please try again later or contact support to resend the activation link.
    </div>
  )
}

export default EmailError
