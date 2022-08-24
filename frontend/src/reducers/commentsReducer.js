import {
    GET_VIDEO_COMMENTS,
    ITEMS_LOADING,
    CLEAR_COMMENTS,
    GET_NEXT_COMMENTS,
    LOAD_COMMENT_REPLIES,
    LOAD_NEXT_REPLIES,
} from '../actions/types';

const initialState = {
    loading: false,
    comments: [],
    nextPageToken: null,
};

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
    switch (action.type) {
        case ITEMS_LOADING:
            return {
                ...state,
                loading: true,
            };
        case GET_VIDEO_COMMENTS:
            return {
                ...state,
                comments: action.payload.items,
                nextPageToken: action.payload.nextPageToken,
                loading: false,
            };
        case GET_NEXT_COMMENTS:
            return {
                ...state,
                comments: [...state.comments, ...action.payload.items],
                nextPageToken: action.payload.nextPageToken,
                loading: false,
            };
        case LOAD_COMMENT_REPLIES:
            return {
                ...state,
                comments: state.comments.map((comment) => {
                    if (comment.id === action.payload.parent_id) {
                        comment.replies = action.payload.replies;
                        return comment;
                    }
                    return comment;
                }),
            };
        case LOAD_NEXT_REPLIES:
            return {
                ...state,
                comments: state.comments.map((comment) => {
                    if (comment.id === action.payload.parent_id) {
                        comment.replies.etag = action.payload.replies.etag;
                        comment.replies.kind = action.payload.replies.kind;
                        comment.replies.pageInfo =
                            action.payload.replies.pageInfo;
                        if (!action.payload.replies.nextPageToken) {
                            delete comment.replies.nextPageToken;
                        } else {
                            comment.replies.nextPageToken =
                                action.payload.replies.nextPageToken;
                        }
                        comment.replies.items = [
                            ...comment.replies.items,
                            ...action.payload.replies.items,
                        ];
                        return comment;
                    }
                    return comment;
                }),
            };
        case CLEAR_COMMENTS:
            return {
                ...state,
                comments: [],
            };
        default:
            return state;
    }
}
