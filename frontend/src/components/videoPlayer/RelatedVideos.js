import { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import ErrorAlert from '../ErrorAlert'
import InfoModal from '../../components/InfoModal';
import { loadRelatedVideos } from '../../actions/playerActions';

const RelatedVideos = ({ video, vp, err, loadRelatedVideos }) => {
    const [showInfoModal, setShowInfoModal] = useState(false);
    const [relatedVideos, setRelatedVideos] = useState(null);
    const tooltipText = 'Save to bookmarks?';

    useEffect(() => {
        if (video?.video?.video_id && !vp?.related_videos) {
            loadRelatedVideos(video?.video?.video_id);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [video.video.video_id]);

    useEffect(() => {
        if (vp?.related_videos) {
            setRelatedVideos(vp.related_videos);
        }
    }, [vp.related_videos]);

    const handleRelatedVideo = (video_id) => {
        setShowInfoModal(true);
        const show_modal = setTimeout(() => {
            setShowInfoModal(false);
        }, 3000);
        return () => {
            clearTimeout(show_modal);
        };
    };
    // console.log(vp.related_videos);
    // console.log(video.video.video_id);
    // console.log(err)

    return (
        <>
            {' '}
            {showInfoModal && <InfoModal content={'Clicked'} />}
            <div className="channel-playlists">
                <h4>Related videos</h4>
                {err.id==='RELATED_VIDEOS_ERROR' && <ErrorAlert />}
                {relatedVideos &&
                    relatedVideos?.items?.map((item) => {
                        // console.log(playlist);
                        return (
                            item?.snippet && (
                                <div
                                    key={item.etag}
                                    className="ch-pl-container"
                                >
                                    <div
                                        className="ch-pl-image-container"
                                        data-text={tooltipText}
                                        onClick={() => {
                                            handleRelatedVideo(item.id.videoId);
                                        }}
                                    >
                                        <p className="ch-pl-count">
                                            {item?.snippet?.channelTitle}
                                        </p>
                                        <img
                                            src={
                                                item?.snippet?.thumbnails
                                                    ?.medium?.url
                                            }
                                            alt={item.id.videoId}
                                        />
                                    </div>
                                    <div className="ch-pl-body">
                                        <p className="ch-pl-title">
                                            {item?.snippet?.title}
                                        </p>
                                        {/* <p className="ch-pl-description">
                                        <FormatText
                                            description={
                                                playlist.snippet.description
                                            }
                                            noloader={true}
                                        />
                                    </p> */}
                                    </div>
                                </div>
                            )
                        );
                    })}
            </div>
        </>
    );
};

const mapStateToProps = (state) => ({
    video: state.ytv,
    vp: state.player,
    err: state.error
});

export default connect(mapStateToProps, { loadRelatedVideos })(RelatedVideos);
