import { GET_SUCCESS, CLEAR_SUCCESS } from '../actions/types'

const initialState = {
  msg: {},
  status: null,
  id: null,
}

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
  switch (action.type) {
    case GET_SUCCESS:
      return {
          msg: action.payload.msg,
          status: action.payload.status,
          id: action.payload.id,
      }
    case CLEAR_SUCCESS:
      return {
        msg:{},
        status: null,
        id: null,
      }
    default:
      return state
  }
}
