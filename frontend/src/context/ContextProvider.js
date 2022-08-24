import { createContext, useContext, useState, useRef, useEffect } from 'react'
import { connect } from 'react-redux'
import { clearPlayer } from '../actions/playerActions';
import {
    closeVideo,
    clearVideo,
    clearList,
} from '../actions/ytvActions';

const StateContext = createContext()
const initialState = {
    commentOrder: 'relevance',
}

const ContextProvider = ({
    children,
    vp,
    video,
    currCategory,
    closeVideo,
    clearVideo,
    clearList,
    clearPlayer,
}) => {

    const [commentOrder, setCommentOrder] = useState(initialState.commentOrder);
    const [showtimestamps, setShowtimestamps] = useState(false);
    const [loading, setLoading] = useState(false);
    const [showComments, setShowComments] = useState(true);
    const [timestampBtn, setTimestampBtn] = useState(true);
    const [timestampControl, setTimestampControl] = useState(true);
    const [showlist, setShowlist] = useState(false);
    const [showdesc, setShowdesc] = useState(true);
    const [previousTimestamp, setPreviousTimestamp] = useState(null);
    const [isLastComment, setIsLastComment] = useState(false);
    const [authTokens, setAuthTokens] = useState(null);
    const [timestampClicked, setTimestampClicked] = useState(false);
    const btnRef = useRef();
    const [newsize, setNewsize] = useState(localStorage.getItem('ytpz') || 3);
    const [newwidth, setNewwidth] = useState(localStorage.getItem('ytpw'));
    const playerInfo = vp?.player?.playerInfo;
    const timestampPreviousTime = (prevTime) => {
        setPreviousTimestamp(prevTime);
    };

    // closes player and saves bookmark data
    const closeCurrentVideo = () => {
        if (playerInfo) {
            localStorage.setItem('playerVolume', playerInfo?.volume);
            video.video.start_at = playerInfo && Number(
                vp?.player?.getCurrentTime()
            );
            const data = {
                video_data: video?.video,
            };
            setShowlist(false);
            closeVideo(video?.video?.id, data, currCategory);
            clearVideo();
            clearPlayer();
            // clearList();
            setPreviousTimestamp(null);
            setShowtimestamps(false);

        }
    };

    const handleCommentOrder = (e) => {
        e.preventDefault();
        setCommentOrder(e.target.value);
    };

    const handleSizeChange = (e) => {
        setNewsize(e);
        const currentW = e || 3;
        const calcW = 10 / Number(currentW);
        const w = window.screen.width / calcW;
        localStorage.setItem('ytpz', e);
        localStorage.setItem('ytpw', w);
        setNewwidth(Number(w));
        // setWidth(w)
    };


    useEffect(() => {
        if (vp?.player) vp?.player?.setSize(newwidth, newwidth * 0.6);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [newsize, newwidth, vp?.player]);

    return (
        <StateContext.Provider
            value={{
                commentOrder,
                setCommentOrder,
                showtimestamps,
                setShowtimestamps,
                loading,
                setLoading,
                showComments,
                setShowComments,
                timestampBtn,
                setTimestampBtn,
                timestampControl,
                setTimestampControl,
                showlist,
                setShowlist,
                showdesc,
                setShowdesc,
                previousTimestamp,
                setPreviousTimestamp,
                timestampPreviousTime,
                isLastComment,
                setIsLastComment,
                btnRef,
                handleCommentOrder,
                authTokens,
                setAuthTokens,
                handleSizeChange,
                newwidth,
                setNewwidth,
                newsize,
                setNewsize,
                timestampClicked,
                setTimestampClicked,
                closeCurrentVideo,
            }}
        >
            {children}
        </StateContext.Provider>
    );
};

const mapStateToProps = (state) => ({
    vp: state.player,
    video: state.ytv,
    currCategory: state.bm.activeCategory,
});

export default connect(mapStateToProps, {
    closeVideo,
    clearVideo,
    clearList,
    clearPlayer,
})(ContextProvider);

export const useStateContext = () => useContext(StateContext)
