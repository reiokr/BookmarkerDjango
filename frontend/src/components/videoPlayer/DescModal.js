import { CgCloseO } from 'react-icons/cg'
import PropTypes from 'prop-types'
import FormatText from './FormatText'
import {connect} from 'react-redux'
import { clearVideoData } from '../../actions/bmActions'


const DescModal = ({
    handleTitle,
    clearVideoData,
    videoData,
    video_length,
}) => {

    // console.log(videoData)
    return (
        <div className="description-container">
            <div className="description-modal">
                <div className="close-btn-bm">
                    <CgCloseO
                        className="close-icon"
                        onClick={() => {
                            clearVideoData()
                            handleTitle()
                        }}
                    />
                </div>
                <div className="modal-body">
                    <FormatText
                        description={videoData.description}
                        videoInfo={videoData}
                        video_length={video_length}
                    />
                </div>
                {videoData.bm_type === 'bm' && (
                    <div className="modal-images">
                        {videoData.thumbnails.map((image, i) => {
                            if (image.src.match(/.*.(jpg|jpeg)/)) {
                                return (
                                    <div
                                        key={image.filename + i}
                                        className="modal-img"
                                    >
                                        <a
                                            href={
                                                /.*.(jpg|jpeg)/.exec(
                                                    image.src
                                                )[0]
                                            }
                                        >
                                            <img
                                                src={
                                                    /.*.(jpg|jpeg)/.exec(
                                                        image.src
                                                    )[0]
                                                }
                                                alt={image.filename}
                                            />
                                        </a>
                                    </div>
                                )
                            }
                            return null
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}

DescModal.defaultProps = { description: 'No description' }
DescModal.propTypes = {
    handleTitle: PropTypes.func.isRequired,
    description: PropTypes.string,
}

const mapStateToProps = (state) => ({

})

export default connect(mapStateToProps, { clearVideoData })(DescModal)
