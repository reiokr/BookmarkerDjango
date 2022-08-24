import {
  CLEAR_VIDEO,
  GET_LIST,
  CLEAR_LIST,
  LIST_LOADING,
  STOP_LOADING,
  LOAD_VIDEO,
  UPDATE_VIDEO,
} from '../actions/types';

const initialState = {
  video: null,
  list: null,
  listloading: false,
};

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
  switch (action.type) {
    case LIST_LOADING:
      return {...state, listloading: true };

    case STOP_LOADING:
      return { ...state, listloading: false };

    case LOAD_VIDEO:
      return { ...state, video: action.payload };

    case UPDATE_VIDEO:
      return { ...state, video: action.payload };

    case GET_LIST:
      return {
        ...state,
        list: {
          items: action.payload.list.map((item) => {
            return item;
          }),
          id: action.payload.list_id,
          listloading: false,
        },
      };

    case CLEAR_LIST:
      return { ...state, list: null };

    case CLEAR_VIDEO:
      return { ...state, video: null };

    default:
      return state;
  }
}
