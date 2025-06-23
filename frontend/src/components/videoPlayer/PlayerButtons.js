import { useState,useEffect } from 'react';
import { connect } from 'react-redux';
import { getList } from '../../actions/ytvActions';
import { load_video_comments } from '../../actions/commentsActions';
import { useTranslation } from 'react-i18next';
import { MdOutlinePreview } from 'react-icons/md';
import { AiOutlineComment, AiOutlineLike } from 'react-icons/ai';
import { ImYoutube2 } from 'react-icons/im';
import { GiDuration } from 'react-icons/gi';
import moment from 'moment';
import { useStateContext } from '../../context/ContextProvider';

const PlayerButtons = ({
    video,
    video_length,
    load_video_comments,
    vp,
    comments,
    handleRateVideo,
}) => {
    const {
        showComments,
        timestampBtn,
        setIsLastComment,
        setShowdesc,
        showdesc,
        setShowlist,
        showlist,
        setShowComments,
        commentOrder,
        showtimestamps,
        setShowtimestamps,
    } = useStateContext();
    const { t } = useTranslation();
    const [commentCount, setCommentCount] = useState(null);

useEffect(() => {
  if(comments?.pageInfo?.totalResults){
    setCommentCount((prev) => comments?.pageInfo?.totalResults);
  }else{
    if(video?.video?.comment_count) setCommentCount(video?.video?.comment_count);
  }
}, [
    comments?.pageInfo?.totalResults,
    video?.video?.comment_count,
]);

    const handleDescription = () => {
        setShowdesc((prev) => !prev);
    };

    const handleTimestampsModal = () => {
        setShowtimestamps((prev) => !prev);
    };

    const handleLoadComments = () => {
        setIsLastComment(false);
        const video_id = vp?.player?.playerInfo?.videoData?.video_id;
        if (comments?.comments.length === 0) {
            if (video_id && commentOrder) {
                load_video_comments(video_id, commentOrder);
            }
        }
        setShowComments((prev) => !prev);
    };

    return (
        <div className="buttons">
            <button
                onClick={handleDescription}
                className={
                    showdesc
                        ? `btn btn-description`
                        : `btn btn-description btn-active`
                }
            >
                {showdesc ? t('Show description') : t('Hide description')}
            </button>
            {video?.video?.list_id && (
                <button
                    className={
                        !showlist
                            ? `btn btn-description`
                            : `btn btn-description btn-active`
                    }
                    onClick={() => setShowlist((prev) => !prev)}
                >
                    {showlist ? t('Hide playlist') : t('Show playlist')}
                    <span className="playlist-length">
                        {vp?.player?.playerInfo?.playlist?.length} videos
                    </span>
                </button>
            )}
            {timestampBtn && (
                <button
                    type="button"
                    id="timestamps"
                    className={
                        !showtimestamps
                            ? `btn btn-description`
                            : `btn btn-description btn-active`
                    }
                    onClick={handleTimestampsModal}
                >
                    {t('Timestamps')}
                </button>
            )}

            <span className="video-info-text" data-text={t('Channel link')}>
                <span>
                    <a
                        href={`https://www.youtube.com/channel/${video?.video?.channel_id}`}
                        target="_blank"
                        rel="noreferrer"
                    >
                        {video?.video?.channel_title}
                    </a>
                </span>
            </span>
            <span className="video-info-text" data-text={t('Published')}>
                <span>
                    {moment(video?.video?.publish_date).format('MMM Do YYYY')}
                </span>
            </span>
            <span className="video-info-text" data-text={t('Duration')}>
                <GiDuration />
                <span> {video_length}</span>
            </span>
            <span
                className="video-info-text"
                data-text={t('Like')}
                onClick={handleRateVideo}
            >
                <AiOutlineLike />
                <span> {video?.video?.like_count}</span>
            </span>
            <span
                className="video-info-text show-comments"
                data-text={
                    showComments ? t('Hide Comments') : t('Show Comments')
                }
                onClick={handleLoadComments}
            >
                <AiOutlineComment />
                <span> {commentCount}</span>
            </span>
            <span className="video-info-text" data-text={t('Views')}>
                <MdOutlinePreview />
                <span> {video?.video?.view_count}</span>
            </span>
            {video?.video?.bm_type === 'yt' && (
                <div className="descmodal-link">
                    <a href={video?.video.url} target="_blank" rel="noreferrer">
                        <ImYoutube2 className="youtube-icon" />
                    </a>
                </div>
            )}
        </div>
    );
};

const mapStateToProps = (state) => ({
    video: state.ytv,
    comments: state.comments,
    vp: state.player,
});

export default connect(mapStateToProps, { getList, load_video_comments })(
    PlayerButtons
);
