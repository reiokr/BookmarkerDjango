import { useEffect, useState, useRef, useCallback } from 'react';
import { connect } from 'react-redux';
import ErrorAlert from '../ErrorAlert';
import InfoModal from '../../components/InfoModal';
import { loadRelatedVideos } from '../../actions/playerActions';
import { addBookmark } from '../../actions/bmActions';
import moment from 'moment';
import { useStateContext } from '../../context/ContextProvider';
import CategoriesModal from './CategoriesModal';

const RelatedVideos = ({ video, vp, err, loadRelatedVideos, addBookmark }) => {
    const {
        handleGoToYouTube,
        handleCategoriesModal,
        activeId,
        setActiveId,
        related_videos_btn_click,
        showCategories,
        bookmarkType,
        showInfoModal,
    } = useStateContext();

    const [relatedVideos, setRelatedVideos] = useState(null);
    const bookmark_ref = useRef();
    const play_ref = useRef();
    const youTube_ref = useRef();

    // console.log(relatedVideos);

    const handleLoadRelatedVideos = useCallback(() => {
        if (video?.video?.video_id && !relatedVideos) {
            loadRelatedVideos(video?.video?.video_id);
        }
    }, [loadRelatedVideos, relatedVideos, video?.video?.video_id]);

    useEffect(() => {
        handleLoadRelatedVideos();
    }, [handleLoadRelatedVideos, video.video.video_id]);

    useEffect(() => {
        if (vp?.related_videos) {
            setRelatedVideos(vp.related_videos);
        }
    }, [vp.related_videos]);

    return (
        <>
            {' '}
            {showInfoModal && bookmarkType === 'video' && (
                <InfoModal content={'Video saved to '} />
            )}
            {vp?.related_videos?.items?.length > 0 && (
                <div className="channel-playlists">
                    <h4>Related videos</h4>
                    <div className="channel-playlists-body">
                        {err.id === 'RELATED_VIDEOS_ERROR' && <ErrorAlert />}
                        {relatedVideos &&
                            relatedVideos?.items?.map((item) => {
                                // console.log(item);
                                return (
                                    item?.snippet && (
                                        <div
                                            key={item.etag}
                                            className="ch-pl-container"
                                        >
                                            {activeId === item.id.videoId &&
                                                showCategories && (
                                                    <CategoriesModal />
                                                )}
                                            <p className="ch-pl-channel-title">
                                                {item.snippet.channelTitle}
                                            </p>
                                            <div className="ch-pl-image-container">
                                                <div
                                                    className="related-videos-btn"
                                                    id={item.id.videoId}
                                                    onClick={
                                                        related_videos_btn_click
                                                    }
                                                    onMouseLeave={(e) => {
                                                        e.target.classList.remove(
                                                            'active'
                                                        );
                                                    }}
                                                >
                                                    <span
                                                        id="h"
                                                        ref={bookmark_ref}
                                                        onClick={() => {
                                                            handleCategoriesModal(
                                                                item.id.videoId,
                                                                'video'
                                                            );
                                                        }}
                                                    >
                                                        <p className="icon">
                                                            Bookmark
                                                        </p>
                                                    </span>
                                                    <span
                                                        id="e"
                                                        ref={youTube_ref}
                                                        onClick={() => {
                                                            handleGoToYouTube(
                                                                item.id.videoId,
                                                                'https://www.youtube.com/watch?v='
                                                            );
                                                            setActiveId(null);
                                                        }}
                                                    >
                                                        <p className="icon">
                                                            YouTube
                                                        </p>
                                                    </span>
                                                    <span
                                                        id="o"
                                                        ref={play_ref}
                                                        onClick={() => {
                                                            setActiveId(null);
                                                        }}
                                                    >
                                                        <p className="icon">
                                                            Play
                                                        </p>
                                                    </span>
                                                </div>
                                                <img
                                                    src={
                                                        item?.snippet
                                                            ?.thumbnails?.medium
                                                            ?.url
                                                    }
                                                    alt={item.id.videoId}
                                                />
                                            </div>
                                            {/* </a> */}
                                            <div className="ch-pl-body">
                                                <p className="ch-pl-title">
                                                    {item?.snippet?.title}
                                                </p>
                                                <p className="ch-pl-published">
                                                    {moment(
                                                        item.snippet.publishedAt
                                                    ).format('MMM Do YYYY')}
                                                </p>
                                            </div>
                                        </div>
                                    )
                                );
                            })}
                    </div>
                </div>
            )}
        </>
    );
};

const mapStateToProps = (state) => ({
    video: state.ytv,
    vp: state.player,
    err: state.error,
});

export default connect(mapStateToProps, { loadRelatedVideos, addBookmark })(
    RelatedVideos
);
