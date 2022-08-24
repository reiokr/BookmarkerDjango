import { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import Comment from './Comment';
import parse from 'html-react-parser';
import { useFindAndReplace } from './script/findAndReplace';
import moment from 'moment';
import { useTranslation } from 'react-i18next';
import { TiArrowSortedDown, TiArrowSortedUp } from 'react-icons/ti';
import { loadReplyList, loadNextReplies } from '../../actions/commentsActions';
import { AiOutlineComment, AiOutlineLike } from 'react-icons/ai';

const TopComment = ({ comment, comments, loadReplyList, loadNextReplies }) => {
    const [showReplies, setShowReplies] = useState(false);
    const { t } = useTranslation();
    const [replyList, setReplyList] = useState(null);

    useEffect(() => {
        comment?.replies && setReplyList(comment?.replies?.comments);
 
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        if (comment?.replies) {
            if (comment?.replies.items) {
                setReplyList(comment?.replies?.items);
            } else {
                setReplyList(comment?.replies?.comments);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [comments.comments, comment]);

    const handleReplyList = async () => {
        if (comment?.snippet?.totalReplyCount > 5 && replyList?.length < 11) {
            loadReplyList(comment?.id);
        }
    };

    const handleMoreReplies = () => {
        loadNextReplies(comment?.id, comment?.replies?.nextPageToken);
    };

    return (
        <div key={comment?.id} className="comment-body">
            <div className="comment-img">
                <img
                    src={
                        comment?.snippet.topLevelComment.snippet
                            .authorProfileImageUrl
                    }
                    alt={
                        comment?.snippet.topLevelComment.snippet
                            .authorDisplayName
                    }
                />
            </div>
            <div className="comment">
                <div className="comment-author">
                    <span className="author-name">
                        {
                            comment?.snippet.topLevelComment.snippet
                                .authorDisplayName
                        }
                    </span>
                    <span className="comment-published">
                        {moment(
                            comment?.snippet.topLevelComment.snippet.publishedAt
                        ).format('MMM Do YYYY')}
                    </span>

                    <span className="comment-likes">
                        <span className="comment-replies-like-icon">
                            <AiOutlineLike />
                        </span>
                        {comment?.snippet.topLevelComment.snippet.likeCount !==
                            0 &&
                            comment?.snippet.topLevelComment.snippet.likeCount}
                    </span>
                </div>
                <div className="comment-text">
                    {parse(
                        useFindAndReplace(
                            comment?.snippet.topLevelComment.snippet.textDisplay
                        )
                    )}
                </div>

                <div className="comment-info">
                    {comment?.replies && (
                        <div
                            className="comment-replies-btn"
                            onClick={() => {
                                setShowReplies(!showReplies);
                            }}
                        >
                            <span className="comment-icon-arrow">
                                {showReplies ? (
                                    <TiArrowSortedUp />
                                ) : (
                                    <TiArrowSortedDown />
                                )}
                            </span>
                            <span>
                                {showReplies ? (
                                    <span className="comment-replies-count">
                                        {t('Hide replies')}
                                        <span className="comment-count">
                                            <span className="comment-replies-icon">
                                                <AiOutlineComment />
                                            </span>
                                            {comment?.snippet?.totalReplyCount}
                                        </span>
                                    </span>
                                ) : (
                                    <span
                                        onClick={handleReplyList}
                                        className="comment-replies-count"
                                    >
                                        {t('Show replies')}
                                        <span className="comment-count">
                                            <span className="comment-replies-icon">
                                                <AiOutlineComment />
                                            </span>
                                            <span className="commnet-counter">
                                                {
                                                    comment?.snippet
                                                        ?.totalReplyCount
                                                }
                                            </span>
                                        </span>
                                    </span>
                                )}
                            </span>
                        </div>
                    )}
                </div>
                {comment.replies && showReplies && (
                    <div className="comment-replies">
                        {replyList &&
                            replyList
                                .sort(
                                    (a, b) =>
                                        Date.parse(a.snippet.publishedAt) -
                                        Date.parse(b.snippet.publishedAt)
                                )
                                .map((comment) => {
                                    return (
                                        <Comment
                                            key={comment.id}
                                            comment={comment}
                                        />
                                    );
                                })}
                        <div className="comment-replies-hide-btn">
                            <div
                                className="hide-replies"
                                onClick={() => {
                                    setShowReplies(!showReplies);
                                }}
                            >
                                <span className="comment-icon-arrow">
                                    <TiArrowSortedUp />
                                </span>
                                <span>{t('Hide replies')}</span>
                            </div>
                            {comment?.replies.nextPageToken && (
                                <span
                                    onClick={() =>
                                        handleMoreReplies(
                                            comment.id,
                                            comment.replies.nextPageToken
                                        )
                                    }
                                    className="more-replies"
                                >
                                    {t('...more')}
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const mapStateToProps = (state) => ({
    comments: state.comments,
    video: state.video,
});

export default connect(mapStateToProps, { loadReplyList, loadNextReplies })(
    TopComment
);
