import { useEffect, useCallback, useState } from 'react'
import { CgCloseO } from 'react-icons/cg'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'
import { getList, updateVideo } from '../../actions/ytvActions'
import moment from 'moment'
import '../../css/Bm.css'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import img from '../../default-img.gif'

const PlaylistModal = ({
    list_id,
    handlePlaylist,
    getList,
    video,
    updateVideo,
    currCategory,
    videoID,
    video_id,
    start_at,
    time,
}) => {
    const [playlist, setPlaylist] = useState([])


    useEffect(() => {
        getList(list_id)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        if (video?.list?.items) {
            setPlaylist(video.list.items)
        }
    }, [video])

    const updateVideoData = useCallback(
        (item) => {
            let startAt = 0
            if (item.video_id === video_id) {
                startAt = start_at
            }
            // update database
            const data = {
                video_id: item.video_id,
                list_id: list_id,
                list_index: item.list_index,
                start_at: startAt,
                category: currCategory,
                url: 'https://youtu.be/' + item.video_id,
            }
            updateVideo(videoID, data, currCategory)
            handlePlaylist()
        },
        [
            currCategory,
            handlePlaylist,
            list_id,
            start_at,
            updateVideo,
            videoID,
            video_id,
        ]
    )

    return (
        <div className="description-container">
            <div className="modal_playlist">
                <div className="description-modal">
                    <div className="close-btn-bm">
                        <CgCloseO
                            className="close-icon"
                            onClick={handlePlaylist}
                        />
                    </div>
                    {playlist !== [] &&
                        playlist.map((item) => {
                            return (
                                <div
                                    key={item.video_id}
                                    className={`${
                                        item.video_id !== video_id
                                            ? 'modal_playlist_item'
                                            : 'modal_playlist_item active'
                                    } ${
                                        item.title.toLowerCase() ===
                                            'private video' && 'private'
                                    }`}
                                    onClick={() => updateVideoData(item)}
                                >
                                    <p
                                        style={{
                                            textAlign: 'right',
                                            width: '20px',
                                        }}
                                    >
                                        {item.video_id !== video_id ? (
                                            item.list_index + 1
                                        ) : (
                                            <PlayArrowIcon
                                                style={{
                                                    color: 'rgb(204, 0, 0)',
                                                }}
                                            />
                                        )}
                                    </p>
                                    <img
                                        style={{
                                            maxWidth: '120px',
                                            maxHeight: '90px',
                                        }}
                                        src={
                                            item.thumbnails.default?.url || img
                                        }
                                        alt={item.title}
                                    />
                                    <div className="video-info-playlist">
                                        <h4>{item.title}</h4>
                                        {item.video_id === video_id && (
                                            <p>
                                                Video start at:{' '}
                                                {time ? time : '00:00'}
                                            </p>
                                        )}
                                        <p>
                                            Published:{' '}
                                            {moment(item.published_at).format(
                                                'MMM Do YYYY'
                                            )}
                                        </p>
                                    </div>
                                </div>
                            )
                        })}
                </div>
            </div>
        </div>
    )
}

const mapStateToProps = (state) => ({
    video: state.ytv,
    currCategory: state.bm.activeCategory,
})

PlaylistModal.propTypes = {
    video: PropTypes.object.isRequired,
}

export default connect(mapStateToProps, { getList, updateVideo })(PlaylistModal)
