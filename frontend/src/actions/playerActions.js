import {
    LOAD_PLAYER,
    CLEAR_PLAYER,
    LOAD_CHANNEL_PLAYLISTS,
    LOAD_MORE_CHANNEL_PLAYLISTS,
    LOAD_RELATED_VIDEOS,
} from './types';
import { tokenConfig } from './authActions';
import { returnErrors } from './errorActions';
import axios from 'axios';

const loadPlayer = (player) => (dispatch) => {
    dispatch({ type: LOAD_PLAYER, payload: player });
};

const clearPlayer = () => (dispatch) => {
    dispatch({ type: CLEAR_PLAYER });
};

const loadChannelPlaylists = (channel_id) => async (dispatch, getState) => {
    try {
        const res = await axios(
            `api/channel/playlists/${channel_id}`,
            tokenConfig(getState, 'get')
        );
        dispatch({ type: LOAD_CHANNEL_PLAYLISTS, payload: res.data });
    } catch (error) {
        console.log(error);
        returnErrors(dispatch({ type: '' }));
    }
};

const loadMoreChannelPlaylists =
    (channel_id, token) => async (dispatch, getState) => {
        try {
            const res = await axios(
                `api/channel/next-playlists/${channel_id}/${token}`,
                tokenConfig(getState, 'get')
            );
            // console.log(res.data)
            dispatch({ type: LOAD_MORE_CHANNEL_PLAYLISTS, payload: res.data });
        } catch (error) {}
    };

const loadRelatedVideos = (video_id) => async (dispatch, getState) => {
    try {
        const res = await axios(
            `api/video/${video_id}/related-videos`,
            tokenConfig(getState, 'get')
        );
        dispatch({ type: LOAD_RELATED_VIDEOS, payload: res.data });
    } catch (err) {
        dispatch(
            returnErrors(
                err.resp,
                err.resp.status,
                'RELATED_VIDEOS_ERROR'
            )
        );
    }
};

export {
    loadPlayer,
    clearPlayer,
    loadChannelPlaylists,
    loadRelatedVideos,
    loadMoreChannelPlaylists,
};
