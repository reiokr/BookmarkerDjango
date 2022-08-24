import {
    GET_BOOKMARKS,
    ADD_BM,
    ITEMS_LOADING,
    DELETE_ITEM,
    URL_ERROR,
    ACTIVE_CATEGORY,
    SEARCH_ITEM,
    SORT_ITEMS,
    STOP_LOADING,
    GET_VIDEO,
    CLEAR_VIDEO,
} from './types'

import { tokenConfig, authError } from './authActions'
import { returnErrors } from './errorActions'
import axios from 'axios'
import defaultImage from '../default-img.gif'

const stopLoading = () => (dispatch) => {
    dispatch({ type: STOP_LOADING })
}

const getBookmarks = (category) => async (dispatch, getState) => {
    try {
        dispatch({ type: ITEMS_LOADING })
        if (category) {
            const res = await axios(
                `/api/bm/${category}`,
                tokenConfig(getState, 'get')
            )
            if (res.data.image_url === null) {
                res.data.image_url = 'http://localhost:8000/' + defaultImage
            }
            // console.log(res.data)
            dispatch({ type: GET_BOOKMARKS, payload: res.data })
        }
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        dispatch({ type: GET_BOOKMARKS, payload: [] })
        dispatch(
            returnErrors(
                err.response?.data,
                err.response?.status,
                'GET_BM_ERROR'
            )
        )
    }
}

const addBookmark = (bookmark) => async (dispatch, getState) => {
    try {
        dispatch({ type: ITEMS_LOADING })
        const res = await axios(
            `/api/bm`,
            tokenConfig(getState, 'post', bookmark)
        )
        if (res.data.error) {
            dispatch({ type: URL_ERROR, payload: res.data })
        } else {
            dispatch({ type: ADD_BM, payload: res.data })
        }
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        dispatch(stopLoading())
        dispatch(
            returnErrors(
                await err.response?.data,
                err.response?.status,
                'ADD_BM_ERROR'
            )
        )
    }
}

const addPlaylistToBookmarks =(pl_id, category) => async (dispatch, getState) => {
  try {
    const res = await axios(`/api/add-playlist-to-bookmarks/${pl_id}`, tokenConfig(getState,'get'));

    const bookmark = {
        url: `https://www.youtube.com/watch?v=${res.data.items[0].contentDetails.videoId}&list=${pl_id}`,
        category,
    };
    // console.log(bookmark)
    dispatch(addBookmark(bookmark))
  } catch (error) {
    console.log(error)
  }

}

const filterBookmarks = (word, category) => async (dispatch, getState) => {
    try {
        dispatch({ type: ITEMS_LOADING })
        let url = ''
        if (word === '') {
            url = `/api/bm/${category}`
        } else {
            url = `/api/bm/${category}/${word}`
        }
        const res = await axios(url, tokenConfig(getState, 'get'))

        const action_data = { bookmarks: res.data, word: word }

        dispatch({
            type: SEARCH_ITEM,
            payload: action_data,
        })
        // console.log(res.data)
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        const action_data = { bookmarks: [], word: word }
        if (err.response.status === 404) {
            dispatch({ type: SEARCH_ITEM, payload: action_data })
        }
        // console.log(err.response)
        dispatch(
            returnErrors(err.response.data, err.response.status, 'FILTER_ERROR')
        )
    }
}

const activeCategory = (category) => async (dispatch, getState) => {
    try {
        if (category) {
            localStorage.setItem('activeCat', category)
            dispatch({ type: ACTIVE_CATEGORY, payload: category })
        }
    } catch (err) {
        dispatch(
            returnErrors(
                err.response.data,
                err.response.status,
                'CATEGORY_ERROR'
            )
        )
    }
}

const deleteItem = (id, category) => async (dispatch, getState) => {
    try {
        // dispatch({ type: ITEMS_LOADING })
        const res = await axios(
            `/api/bm/${id}`,
            tokenConfig(getState, 'delete')
        )
        if (res.status === 204) {
            dispatch({ type: DELETE_ITEM, payload: id })
            dispatch(getBookmarks(category))
        }
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        dispatch(
            returnErrors(err.response.data, err.response.status, 'DELETE_ERROR')
        )
    }
}

const getVideo = (id) => async (dispatch, getState) => {
    try {
        const res = await axios('/api/bm/' + id, tokenConfig(getState))
        dispatch({ type: GET_VIDEO, payload: res.data })
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        console.log(err)
    }
}

const rateVideo = (video_id) => async (dispatch, getState) => {
    try {
        const res = axios(`api/bm/rate/${video_id}`, tokenConfig(getState))
        console.log(res.status)
    } catch (err) {
        if (err.response.status === 401) {
            dispatch(authError())
        }
        console.log(err)
    }
}

const clearVideoData = () => (dispatch) => {
    dispatch({ type: CLEAR_VIDEO })
}

const sortItems = (sort, category) => (dispatch) => {
    dispatch({ type: ITEMS_LOADING })
    dispatch({ type: SORT_ITEMS })
    // dispatch({ type: SORT_ITEMS, payload: sort });
    // dispatch(getBookmarks(category));
}

export {
    getBookmarks,
    addBookmark,
    deleteItem,
    sortItems,
    filterBookmarks,
    activeCategory,
    stopLoading,
    getVideo,
    clearVideoData,
    rateVideo,
    addPlaylistToBookmarks,
};
