import {
    CLEAR_VIDEO,
    GET_LIST,
    CLEAR_LIST,
    STOP_LOADING,
    LOAD_VIDEO,
    UPDATE_VIDEO,
    ITEMS_LOADING,
} from '../actions/types';
import axios from 'axios';
import { getBookmarks } from '../actions/bmActions';
import { tokenConfig } from './authActions';

const closeVideo = (id, video, category) => async (dispatch, getState) => {
    try {
        if (id && video && category) {
            const response = await axios(
                `/api/bm/video/${video.video_data.video_id}`,
                tokenConfig(getState)
            );
            const video_data = response.data;
            video_data.list_id = video.video_data.list_id;
            video_data.list_index = video.video_data.list_index;
            video_data.category = category;
            video_data.start_at = video.video_data.start_at;
            video_data.list_items_count = video.video_data.list_items_count;
            const data = {
                video_data: await video_data,
            };
            await axios(
                `/api/bm/${id}`,
                tokenConfig(getState, 'put', JSON.stringify(data))
            );
            // dispatch({ type: CLOSE_VIDEO, payload: res.data });
            dispatch(getBookmarks(category));
        }
    } catch (err) {
        console.log(err.message);
    }
};

const updateVideo = (id, video, category) => async (dispatch, getState) => {
    try {
        if (id && video) {
            const response = await axios(
                `/api/bm/video/${video.video_id}`,
                tokenConfig(getState)
            );
            const video_data = response.data;
            video_data.list_id = video.list_id;
            video_data.list_index = video.list_index;
            video_data.url = 'https://youtu.be/' + video.video_id;
            video_data.category = category;
            video_data.start_at = video.start_at;
            video_data.list_items_count = video.list_items_count;
            const data = {
                video_data: await video_data,
            };
            const res = await axios(
                `/api/bm/${id}`,
                tokenConfig(getState, 'put', JSON.stringify(data))
            );
            dispatch({ type: UPDATE_VIDEO, payload: res.data });
        }
    } catch (error) {
        console.log(error);
    }
};

const saveVideoInterval = (id, video) => async (dispatch, getState) => {
    try {
        await axios(
            `/api/bm/${id}`,
            tokenConfig(getState, 'put', JSON.stringify(video))
        );
    } catch (error) {
        console.log(error);
    }
};

const getList = (list_id) => async (dispatch, getState) => {
    dispatch({ type: ITEMS_LOADING });
    try {
        const res = await axios(
            `/api/bm/list/${list_id}`,
            tokenConfig(getState)
        );
        // console.log(res.data)
        dispatch({ type: GET_LIST, payload: { list: res.data, list_id } });
        dispatch({ type: STOP_LOADING });
    } catch (err) {
        console.log(err);
        dispatch({ type: CLEAR_LIST });
        dispatch({ type: STOP_LOADING });
    }
};

const loadVideo = (id) => async (dispatch, getState) => {
    try {
        if (id) {
            const res = await axios('/api/bm/' + id, tokenConfig(getState));
            dispatch({ type: LOAD_VIDEO, payload: res.data });
        }
    } catch (err) {
        console.log(err);
    }
};

const clearList = () => (dispatch) => {
    dispatch({ type: CLEAR_LIST });
};

const clearVideo = () => (dispatch) => {
    dispatch({ type: CLEAR_VIDEO });
};

export {
    clearVideo,
    closeVideo,
    getList,
    clearList,
    loadVideo,
    updateVideo,
    saveVideoInterval,
};
