import axios from 'axios';
import jwt from 'jwt-decode';
import {
    USER_LOADED,
    LOGIN_SUCCESS,
    LOGIN_FAIL,
    USER_NOT_ACTIVE,
    LOGOUT_SUCCESS,
    ADD_CATEGORY,
    DELETE_USER,
    SIGN_UP,
    UPDATE_USER_DATA,
    AUTH_ERROR,
    SENDING_EMAIL,
    EMAIL_ERROR
} from './types';
import { returnErrors, clearErrors } from './errorActions';
import { returnSuccess } from './successActions';
import { activeCategory } from './bmActions';

// Setup config headers and token
const tokenConfig = (getState, method, data) => {
    const accessToken = getState().auth.token?.access;
    // console.log(accessToken)
    //Headers
    const config = {
        data: data,
        method: method,
        headers: {
            accept: '*/*',
            'accept-language':
                'et-EE,et;q=0.9,en-EE;q=0.8,en;q=0.7,en-US;q=0.6',
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
    };
    // if token true, add to header
    if (accessToken) config.headers['Authorization'] = 'Bearer ' + accessToken;
    return config;
};

const loadUser = () => async (dispatch, getState) => {
    const accessToken = getState().auth.token?.access;
    if (accessToken) {
        const user = jwt(accessToken);
        // User loading in process
        dispatch({ type: 'USER_LOADING' });
        // Fetch user data from database
        try {
            const res = await axios(
                `/api/users/${user.user_id}`,
                tokenConfig(getState, 'get')
            );
            // console.log(res.data)
            dispatch(returnSuccess(res.data, res.status, 'SIGNUP_SUCCESS'));
            if (res.data) {
                const data = {
                    refresh:
                        JSON.parse(localStorage.getItem('token')).refresh ||
                        getState().auth.token?.refresh,
                };
                const refreshResult = await axios(
                    `/api/login/refresh/`,
                    tokenConfig(getState, 'post', JSON.stringify(data))
                );
                localStorage.setItem(
                    'token',
                    JSON.stringify(refreshResult.data)
                );
            }
            dispatch({ type: USER_LOADED, payload: res.data });
            if ((await res.data.categories.length) === 0) {
                dispatch(updateCategories(['MyCategory']));
            }
            if (!localStorage.getItem('activeCat')) {
                dispatch(activeCategory(res.data.categories[0]));
            }
            // console.log(res.data)
            if (!res.data.options) {
                const data = {
                    theme: 1,
                    loclization: 'en',
                    settings: {},
                };
                dispatch(updateUserOptions(data));
            }
        } catch (error) {
            console.log(error);
        }
    }
};

const signUpUser = (data) => async (dispatch) => {
    const config = {
        method: 'post',
        url: 'api/register/',
        data: data,
    };
    // console.table([...data])
    try {
        dispatch({ type: 'USER_LOADING' });
        dispatch({ type: SENDING_EMAIL });
        const res = await axios(config);
        if (res.data) {
            dispatch({ type: SIGN_UP });
            dispatch(returnSuccess(res.data, res.status, 'SIGNUP_SUCCESS'));
            // localStorage.setItem('ytpw', 840);
            // localStorage.setItem('playerVolume', 50);
            // window.location = '/login';
        }
    } catch (err) {
        dispatch({ type: EMAIL_ERROR });
        dispatch(
            returnErrors(err.response.data, err.response.status, 'SIGNUP_ERROR')
        );
    }
};

const loginUser = (data) => async (dispatch) => {
    var config = {
        method: 'post',
        url: `api/login/`,
        data: data,
    };
    try {
        dispatch({ type: 'USER_LOADING' });
        const res = await axios(config);

        if (res.data.email === 'not_registered') {
            dispatch(returnErrors(res.data.msg, res.data.status, 'LOGIN_FAIL'));
            return dispatch({ type: LOGIN_FAIL, payload: res.data });
        }
        if (res.data.email === 'not_verified') {
            dispatch(
                returnErrors(res.data.msg, res.data.status, 'USER_NOT_ACTIVE')
            );
            return dispatch({ type: USER_NOT_ACTIVE, payload: res.data });
        }
        dispatch({ type: LOGIN_SUCCESS, payload: res.data });
        window.location = '/';
    } catch (err) {
        dispatch(
            returnErrors(err.response.data, err.response.status, 'LOGIN_ERROR')
        );
    }
};

const logout = () => (dispatch) => {
    dispatch({ type: LOGOUT_SUCCESS });
};

const updateUserOptions = (data) => async (dispatch, getState) => {
    try {
        const res = await axios(
            `/api/user/options`,
            tokenConfig(getState, 'put', JSON.stringify(data))
        );
        if (res.data) {
            dispatch(loadUser());
        }
    } catch (err) {
        console.log(err);
    }
};

const updateCategories =
    (updatedCategories, category) => async (dispatch, getState) => {
        const token = getState().auth.token?.access;
        const user = jwt(token);
        const data = { categories: updatedCategories, category: category };

        try {
            const res = await axios(
                `/api/user/categories/${user.user_id}`,
                tokenConfig(getState, 'put', JSON.stringify(data))
            );
            dispatch({ type: ADD_CATEGORY, payload: res.data });
            dispatch(clearErrors());
        } catch (err) {
            dispatch(
                returnErrors(
                    err.response.data,
                    err.response.status,
                    'CATEGORY_ERROR'
                )
            );
        }
    };

const updateUserData = (userdata) => async (dispatch, getState) => {
    const token = getState().auth.token?.access;
    const user = jwt(token);
    let data = userdata;
    try {
        const res = await axios(
            `/api/users/${user.user_id}`,
            tokenConfig(getState, 'put', JSON.stringify(data))
        );
        dispatch({ type: UPDATE_USER_DATA, payload: res.data });
        dispatch(returnSuccess(res.data, res.status, 'UPDATE_USER_SUCCESS'));
    } catch (err) {
        dispatch(
            returnErrors(
                err.response.data,
                err.response.status,
                'UPDATE_USER_ERROR'
            )
        );
    }
};

const deleteUser = (id) => async (dispatch, getState) => {
    try {
        const res = await axios(
            `api/users/${id}`,
            tokenConfig(getState, 'delete')
        );
        if (res.status === 204) {
            dispatch({ type: DELETE_USER });
            dispatch(returnSuccess(res.data, res.status, 'DEL_USER_SUCCESS'));
        }
    } catch (err) {
        dispatch(
            returnErrors(
                err.response.data,
                err.response.status,
                'DEL_USER_ERROR'
            )
        );
    }
};

const authError = () => async (dispatch) => {
    dispatch({ type: AUTH_ERROR });
};

export {
    signUpUser,
    loginUser,
    loadUser,
    tokenConfig,
    logout,
    updateCategories,
    deleteUser,
    updateUserData,
    updateUserOptions,
    authError,
};
