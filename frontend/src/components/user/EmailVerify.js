import { Component } from 'react'
// import { BASE_API_URL, EMAIL_VERIFIED } from '../../config/site'

class EmailVerify extends Component {
    // state = {
    //     valid: 0,
    // }

    // async componentDidMount() {
    //     const token = this.props.match.params.token

    //     if (token) {
    //         this.setState({ token: this.props.match.params.token })

    //         fetch(BASE_API_URL + 'users/validate-email-token', {
    //             method: 'post',
    //             headers: {
    //                 Accept: 'application/json',
    //                 'Content-Type': 'application/json',
    //             },
    //             body: JSON.stringify({
    //                 token: token,
    //             }),
    //         })
    //             .then((res) => res.json())
    //             .then((response) => {
    //                 if (response.status === 'success') {
    //                     this.setState({ valid: 1 })
    //                     localStorage.setItem(EMAIL_VERIFIED, 1)
    //                 } else if (response.status === 'failed') {
    //                     this.setState({ valid: 2 })
    //                 }
    //             })
    //     }
    // }

    // render() {
    //     return (
    //         <div className="container">
    //             <div className="row">
    //                 <div className="col-md-12">
    //                     <div className="custom-alert">
    //                         {this.state.valid === 1 && (
    //                             <div class="alert alert-success" role="alert">
    //                                 <p>Email Verification Done</p>
    //                             </div>
    //                         )}
    //                         {this.state.valid === 2 && (
    //                             <div class="alert alert-danger" role="alert">
    //                                 <p>
    //                                     Email Verification Failed. Email may be
    //                                     already verified or the link is broken.
    //                                 </p>
    //                             </div>
    //                         )}
    //                     </div>
    //                 </div>
    //             </div>
    //         </div>
    //     )
    // }
}

export default EmailVerify
