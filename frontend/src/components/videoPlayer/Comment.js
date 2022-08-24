import parse from 'html-react-parser'
import moment from 'moment'
import { useFindAndReplace } from './script/findAndReplace'
import { AiOutlineLike } from 'react-icons/ai'


const Comment = ({ comment }) => {

    return (
        <div key={comment.id} className="comment-body">
            <div className="comment-img">
                <img
                    src={comment?.snippet.authorProfileImageUrl}
                    alt={comment?.snippet.authorDisplayName}
                />
            </div>
            <div className="comment">
                <div className="comment-author">
                    <span className="author-name">
                        {comment?.snippet.authorDisplayName}
                    </span>
                    <span className="comment-published">
                        {moment(comment?.snippet.publishedAt).format(
                            'MMM Do YYYY'
                        )}
                    </span>
                    <span className="comment-likes">
                        <span className="comment-replies-like-icon">
                            <AiOutlineLike />
                        </span>
                        {comment?.snippet.likeCount !== 0 &&
                            comment?.snippet.likeCount}
                    </span>
                </div>
                <div className="comment-text">
                    {parse(useFindAndReplace(comment?.snippet.textDisplay))}
                </div>
            </div>
        </div>
    );
}

export default Comment
