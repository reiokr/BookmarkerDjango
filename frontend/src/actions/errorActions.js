import { GET_ERRORS, CLEAR_ERRORS } from './types';



const returnErrors = (msg, status, id = null) => {
  return {
    type: GET_ERRORS,
    payload: { msg, status, id },
  };
};

const clearErrors = () => (dispatch) => {
  dispatch({ type: CLEAR_ERRORS });
};

export { returnErrors, clearErrors };
