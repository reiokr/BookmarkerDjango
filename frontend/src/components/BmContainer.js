import { connect } from 'react-redux'
import Bm from './Bm'
import Ytv from './Ytv'
import YTvideoPlayer from './videoPlayer/YTvideoPlayer'
import '../css/Bm.css'
import ErrorAlert from './ErrorAlert'
import Loader from './Loader'
import PropTypes from 'prop-types'
import { useStateContext } from '../context/ContextProvider'

const BmContainer = ({ data, auth, video, err }) => {
    const { newwidth } = useStateContext()
// console.log(auth)

    return (
        <>
            {video?.video?.video_id && auth.isAuthenticated ? (
                <YTvideoPlayer newwidth={newwidth} />
            ) : (
                <div className="container">
                    <div className="category-content">
                        <div style={{ marginTop: '30px' }}>
                            {(err?.id === 'FILTER_ERROR' ||
                                err?.id === 'GET_BM_ERROR') &&
                                data?.bm.length === 0 && <ErrorAlert />}
                        </div>
                        <div className="bm-container">
                            {data.loading && <Loader />}
                            {data?.bm &&
                                data?.bm.map((item) => {
                                    if (item.bm_type === 'bm') {
                                        return <Bm key={item.id} item={item} />
                                    }
                                    if (item.bm_type === 'yt') {
                                        return <Ytv key={item.id} item={item} />
                                    }
                                    return null
                                })}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

const mapStateToProps = (state) => ({
    data: state.bm,
    auth: state.auth,
    video: state.ytv,
    err: state.error,
})

BmContainer.propTypes = {
    data: PropTypes.object.isRequired,
    auth: PropTypes.object.isRequired,
    video: PropTypes.object.isRequired,
    err: PropTypes.object.isRequired,
}

export default connect(mapStateToProps, {})(BmContainer)
