import { connect } from 'react-redux'
import { updateVideo } from '../../actions/ytvActions'
import { clearVideoData } from '../../actions/bmActions'
import TopComment from './TopComment'
import { useTranslation } from 'react-i18next'
import {useStateContext} from '../../context/ContextProvider'
import LdsFacebook from '../LdsFacebook';


const CommentModal = ({ comments }) => {
  const { handleCommentOrder } = useStateContext()
    const { t } = useTranslation()


    return (
        <div className="comment-modal">
            <div className="comment-order">
                <select
                    id="order"
                    onChange={(e) => {
                        handleCommentOrder(e);
                    }}
                >
                    <option value="" style={{ display: 'none' }}>
                        {t('Ordering')}
                    </option>
                    <option style={{ height: '30px' }} value="relevance">
                        {t('Relevance')}
                    </option>
                    <option value="time">{t('Newest first')}</option>
                </select>
            </div>
            {!comments && <LdsFacebook />}

            {comments &&
                comments.map((comment) => {
                    return <TopComment key={comment?.id} comment={comment} />;
                })}
        </div>
    );
}
const mapStateToProps = (state) => ({
    comments: state.comments.comments,
    currCategory: state.bm.activeCategory,
    vp: state.player,
})

export default connect(mapStateToProps, { updateVideo, clearVideoData })(
    CommentModal
)
