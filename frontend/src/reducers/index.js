import { combineReducers } from 'redux';
import bmReducer from './bmReducer';
import errorReducer from './errorReducer';
import authReducer from './authReducer';
import ytvReducer from './ytvReducer';
import playerReducer from './playerReducer';
import successReducer from './successReducer';
import commentsReducer from './commentsReducer';

export default combineReducers({
  bm: bmReducer,
  error: errorReducer,
  success: successReducer,
  auth: authReducer,
  ytv: ytvReducer,
  player: playerReducer,
  comments: commentsReducer
});
