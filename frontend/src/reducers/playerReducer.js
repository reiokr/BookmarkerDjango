import {
    LOAD_PLAYER,
    CLEAR_PLAYER,
    LOAD_CHANNEL_PLAYLISTS,
    LOAD_MORE_CHANNEL_PLAYLISTS,
    LOAD_RELATED_VIDEOS,
} from '../actions/types';

const initialState = {
    player: null,
    channel_playlists: null,
    related_videos: null,
};

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
    switch (action.type) {
        case LOAD_PLAYER:
            return { ...state, player: action.payload };
        case CLEAR_PLAYER:
            return { ...state, player: null };
        case LOAD_CHANNEL_PLAYLISTS:
            return {
                ...state,
                channel_playlists: action.payload,
            };
        case LOAD_RELATED_VIDEOS:
            return { ...state, related_videos: action.payload };
        case LOAD_MORE_CHANNEL_PLAYLISTS:
          return { 
            ...state,
          channel_playlists: {
            etag: action.payload.etag,
            items: [...state.channel_playlists.items,...action.payload.items],
            kind: action.payload.kind,
            nextPageToken: action.payload.nextPageToken,
            pageInfo: action.payload.pageInfo,
          }
          }
        default:
            return state;
    }
}
