import { GET_SUCCESS, CLEAR_SUCCESS } from "./types";
import { stopLoading } from './bmActions';


// Return errors

const returnSuccess = (status, id = null) => {
  return {
    type: GET_SUCCESS,
    payload: { status, id },
  };
};

const clearSuccess = () => (dispatch) => {
  dispatch(stopLoading());
  dispatch({ type: CLEAR_SUCCESS });
};

export { returnSuccess, clearSuccess };
