import {
    USER_LOADED,
    USER_LOADING,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    SIGN_UP,
    UPDATE_USER_DATA,
    ADD_CATEGORY,
    DELETE_USER,
    DELETE_CATEGORY,
    AUTH_ERROR,
    SENDING_EMAIL,
    EMAIL_ERROR,
} from '../actions/types';

const initialState = {
    token: JSON.parse(localStorage.getItem('token')) || null,
    isAuthenticated: null,
    isLoading: false,
    user: null,
    sendingEmail: false,
};

// eslint-disable-next-line import/no-anonymous-default-export
export default function (state = initialState, action) {
    switch (action.type) {
        case USER_LOADING:
            return {
                ...state,
                isLoading: true,
            };
        case AUTH_ERROR:
            return {
                ...state,
                isAuthenticated: null,
            };
        case USER_LOADED:
            return {
                ...state,
                isAuthenticated: true,
                isLoading: false,
                user: action.payload,
            };
        case SIGN_UP:
            return {
                ...state,
                isLoading: false,
                sendingEmail: false,
            };
        case SENDING_EMAIL:
            return {
                ...state,
                sendingEmail: true,
            };
        case EMAIL_ERROR:
            return {
                ...state,
                sendingEmail: false,
            };
        case LOGIN_SUCCESS:
            return {
                ...state,
                token: localStorage.setItem(
                    'token',
                    JSON.stringify(action.payload)
                ),
                isLoading: false,
            };
        case LOGOUT_SUCCESS:
            localStorage.removeItem('token');
            return {
                ...state,
                token: null,
                isAuthenticated: false,
                isLoading: false,
                user: null,
            };
        case ADD_CATEGORY:
            return {
                ...state,
                user: action.payload,
            };
        case DELETE_CATEGORY:
            return {
                ...state,
                categories: action.payload,
            };
        case UPDATE_USER_DATA:
            return {
                ...state,
                user: action.payload,
            };
        case DELETE_USER:
            return {
                ...state,
                user: null,
            };
        default:
            return state;
    }
}
