import {
    GET_BOOKMARKS,
    CLEAR_DATA,
    ADD_BM,
    URL_ERROR,
    ITEMS_LOADING,
    DELETE_ITEM,
    SORT_ITEMS,
    SEARCH_ITEM,
    ACTIVE_CATEGORY,
    STOP_LOADING,
    GET_VIDEO,
    CLEAR_VIDEO,
} from '../actions/types'

const localStorageCategory = localStorage.getItem('activeCat')

const initialState = {
    bm: [],
    sort: true,
    loading: false,
    bmCount: 0,
    isEmptyCategory: true,
    activeCategory: localStorageCategory || '',
    urlError: false,
    videoData: null,
}

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
    switch (action.type) {
        case ITEMS_LOADING:
            return {
                ...state,
                loading: true,
            }
        case STOP_LOADING:
            return { ...state, loading: false }

        case ACTIVE_CATEGORY:
            return {
                ...state,
                activeCategory: action.payload,
                loading: false,
                bmCount: state.bm.length,
            }

        case GET_BOOKMARKS:
            if (state.sort) {
                return {
                    ...state,
                    bm: action.payload.reverse(),
                    isEmptyCategory: action.payload.length === 0 ? true : false,
                    loading: false,
                }
            } else {
                return {
                    ...state,
                    bm: action.payload,
                    loading: false,
                }
            }

        case GET_VIDEO:
            return {
                ...state,
                videoData: action.payload,
            }

        case CLEAR_VIDEO:
          return {
            ...state,
            videoData: null
          }

        case SEARCH_ITEM:
            if (state.sort) {
                return {
                    ...state,
                    bm: action.payload.bookmarks.reverse(),
                    isEmptyCategory:
                        action.payload.bookmarks.length === 0 &&
                        action.payload.word === ''
                            ? true
                            : false,
                    loading: false,
                }
            } else {
                return {
                    ...state,
                    bm: action.payload.bookmarks,
                    isEmptyCategory: false,
                    loading: false,
                }
            }

        case URL_ERROR:
            return {
                ...state,
                urlError: action.payload,
            }

        case ADD_BM:
            return {
                ...state,
                bm: [action.payload, ...state.bm],
                loading: false,
            }

        case DELETE_ITEM:
            return {
                ...state,
                bm: state.bm.filter((item) => item.id !== action.payload),
                loading: false,
            }
        case SORT_ITEMS:
            return { ...state, loading: false, bm: state.bm.reverse() }

        case CLEAR_DATA:
            return {
                ...state,
                bm: [],
                sort: true,
                loading: false,
            }

        default:
            return state
    }
}
