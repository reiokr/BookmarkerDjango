import '../css/Bm.css'
import '../css/Description.css'
import { useState, useEffect } from 'react'
import Fade from '@mui/material/Fade'
import { CgCloseO } from 'react-icons/cg'
import { FcStart } from 'react-icons/fc'
import { MdVideoLibrary } from 'react-icons/md'
import { connect } from 'react-redux'
import { clearList } from '../actions/ytvActions'
import {
    useToHHMMSS,
    useSecondsTo_HHMMSS,
} from './videoPlayer/script/timeConverter'
import { deleteItem, getVideo } from '../actions/bmActions'
import { loadVideo } from '../actions/ytvActions'
import DescModal from './videoPlayer/DescModal'
import DeleteModal from './videoPlayer/DeleteModal'
import PlaylistModal from './videoPlayer/PlaylistModal'
import PropTypes from 'prop-types'
import moment from 'moment'
import { useTranslation } from 'react-i18next'

const Ytv = ({ item, deleteItem, loadVideo, data, clearList, getVideo }) => {
    const {
        title,
        id,
        start_at,
        description,
        bm_type,
        url,
        list_id,
        thumbnails,
        video_id,
        length,
    } = item

    const [showmodal, setShowmodal] = useState(false)
    const [showPlaylist, setShowPlaylist] = useState(false)
    const [deleteModal, setDeleteModal] = useState(false)
    const [titleLoaded, setTitleLoaded] = useState(false)
    const time = useToHHMMSS(start_at)
    const video_length = useSecondsTo_HHMMSS(
        moment.duration(length).asSeconds()
    )
    const { t } = useTranslation()

    const handleVideo = () => {
        loadVideo(id)
    }

    const handleTitle = () => {
        if (!showmodal) getVideo(id)
        setShowmodal((prev) => !prev)
    }

    const handlePlaylist = () => {
        clearList()
        setShowPlaylist((prev) => !prev)
    }

    const handleDelete = () => {
        setDeleteModal((prev) => !prev)
        deleteItem(id, data.activeCategory)
    }

    useEffect(() => {
        if (title) {
            setTitleLoaded(true)
        } else setTitleLoaded(false)
    }, [title])

    return (
        <>
            {showmodal && (
                <DescModal
                    description={description}
                    url={url}
                    type={bm_type}
                    handleTitle={handleTitle}
                    videoData={item}
                    video_length={video_length}
                />
            )}
            {showPlaylist && list_id !== null && (
                <PlaylistModal
                    type={bm_type}
                    handlePlaylist={handlePlaylist}
                    list_id={list_id}
                    videoID={id}
                    video_id={video_id}
                    start_at={start_at}
                    time={time}
                />
            )}
            {deleteModal && (
                <DeleteModal
                    handleDelete={handleDelete}
                    setDeleteModal={setDeleteModal}
                />
            )}
            <Fade in={titleLoaded}>
                <div className="bm-main">
                    <div className="bookmark">
                        <div className="play-video-btn " onClick={handleVideo}>
                            <span className="video-length">{video_length}</span>
                            <span
                                className="video-start"
                                data-content={t('Play video')}
                            >
                                <FcStart className="video-start-icon" />{' '}
                                <p className="start-text">{t('Start at')}</p>
                                <p className="start-time">
                                    {start_at !== null ? time : '00:00'}
                                </p>
                            </span>
                        </div>
                        {list_id !== null && (
                            <div
                                className="playlist-flag"
                                onClick={handlePlaylist}
                                data-text={t('List playlist')}
                            >
                                <MdVideoLibrary />
                                {t('Playlist')}
                            </div>
                        )}
                        <img
                            className="bm-img"
                            src={
                                thumbnails?.maxres?.url
                                    ? thumbnails?.maxres?.url
                                    : thumbnails?.standard?.url
                                    ? thumbnails?.standard?.url
                                    : thumbnails?.high?.url
                            }
                            alt={url}
                        />
                        <div className="title-container">
                            <div
                                className="title"
                                onClick={handleTitle}
                                data-content={t('Show description')}
                            >
                                <p>{title}</p>
                                <div>{t('...more')}</div>
                            </div>
                        </div>
                    </div>
                    <div className="close-btn-ytv">
                        <CgCloseO
                            className="close-icon"
                            onClick={() => setDeleteModal((prev) => !prev)}
                        />
                    </div>
                </div>
            </Fade>
        </>
    )
}

const mapStateToProps = (state) => ({
    data: state.bm,
    videoData: state.bm.videoData,
})

Ytv.propTypes = {
    data: PropTypes.object.isRequired,
    deleteItem: PropTypes.func.isRequired,
    loadVideo: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, {
    deleteItem,
    loadVideo,
    clearList,
    getVideo,
})(Ytv)
