import {
    GET_VIDEO_COMMENTS,
    ITEMS_LOADING,
    CLEAR_COMMENTS,
    GET_NEXT_COMMENTS,
    LOAD_COMMENT_REPLIES,
    LOAD_NEXT_REPLIES,
} from './types'
import { tokenConfig } from './authActions'
import axios from 'axios'

const load_video_comments = (video_id, order) => async (dispatch, getState) => {
    try {
        dispatch({ type: ITEMS_LOADING })
        if (video_id) {
          if(!order) order ='relevance'
            const res = await axios(
                `api/bm/comments/${video_id}/${order}`,
                tokenConfig(getState, 'get')
            )
            // console.log(res.data)
            dispatch({
                type: GET_VIDEO_COMMENTS,
                payload: res.data,
            })
        }
    } catch (error) {
        console.log(error)
    }
}

const load_next_comments =
    (video_id, nextPageToken, order) => async (dispatch, getState) => {
        try {
            dispatch({ type: ITEMS_LOADING })
            if (video_id) {
                const res = await axios(
                    `api/bm/comments/${video_id}/${nextPageToken}/${order}`,
                    tokenConfig(getState, 'get')
                )
                dispatch({ type: GET_NEXT_COMMENTS, payload: res.data })
            }
        } catch (error) {
            console.log(error)
        }
    }

const loadReplyList = (parent_id) => async (dispatch, getState) => {
    try {
        if (parent_id) {
          const res = await axios(`api/bm/comment/replies/${parent_id}`, tokenConfig(getState, 'get'));
          dispatch({
              type: LOAD_COMMENT_REPLIES,
              payload: { replies: res.data, parent_id },
          })
        }
    } catch (error) {
      console.log(error)
    }
}

const loadNextReplies =
    (parent_id, page_token) => async (dispatch, getState) => {
          try {
              if (parent_id) {
                  const res = await axios(
                      `api/bm/comment/nextreplies/${parent_id}/${page_token}`,
                      tokenConfig(getState, 'get')
                  )
                  dispatch({
                      type: LOAD_NEXT_REPLIES,
                      payload: { replies: res.data, parent_id },
                  })
              }
          } catch (error) {
              console.log(error)
          }
    }

const clear_comments = () => async (dispatch) => {
    dispatch({ type: CLEAR_COMMENTS })
}

export {
    load_video_comments,
    clear_comments,
    load_next_comments,
    loadReplyList,
    loadNextReplies,
}
