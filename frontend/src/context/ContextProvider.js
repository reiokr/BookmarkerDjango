import { createContext, useContext, useState, useRef, useEffect } from 'react';
import { connect } from 'react-redux';
import { clearPlayer } from '../actions/playerActions';
import { closeVideo, clearVideo, clearList } from '../actions/ytvActions';
import { addPlaylistToBookmarks, addBookmark } from '../actions/bmActions';

const StateContext = createContext();
const initialState = {
    commentOrder: 'relevance',
};

const ContextProvider = ({
    children,
    vp,
    video,
    auth,
    data,
    currCategory,
    closeVideo,
    clearVideo,
    clearList,
    clearPlayer,
    addPlaylistToBookmarks,
    addBookmark,
}) => {
    const [addCategoryModal, setAddCategoryModal] = useState(false);
    const [isEmptyCategory, setIsEmptyCategory] = useState(false);
    const [commentOrder, setCommentOrder] = useState(initialState.commentOrder);
    const [showtimestamps, setShowtimestamps] = useState(false);
    const [loading, setLoading] = useState(false);
    const [showComments, setShowComments] = useState(false);
    const [timestampBtn, setTimestampBtn] = useState(true);
    const [timestampControl, setTimestampControl] = useState(true);
    const [showlist, setShowlist] = useState(false);
    const [showdesc, setShowdesc] = useState(true);
    const [previousTimestamp, setPreviousTimestamp] = useState(null);
    const [isLastComment, setIsLastComment] = useState(false);
    const [authTokens, setAuthTokens] = useState(null);
    const [timestampClicked, setTimestampClicked] = useState(false);
    const [activeId, setActiveId] = useState(null);
    const [showInfoModal, setShowInfoModal] = useState(false);
    const [showCategories, setShowCategories] = useState(false);
    const [saveToCategory, setSaveToCategory] = useState(false);
    const [categoriesModalSelected, setCategoriesModalSelected] =
        useState(null);
    const [categories, setCategories] = useState([]);
    const [changeActiveCategory, setChangeActiveCategory] = useState(true);
    const [bookmarkType, setBookmarkType] = useState(null);
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
            localStorage.setItem('playerVolume', playerInfo?.volume || 50);
            video.video.start_at =
                playerInfo && Number(playerInfo.currentTime);
            if (playerInfo?.playlist?.length) {
                video.video.list_items_count =
                    playerInfo?.playlist?.length || 0;
            }
            video.video.url = playerInfo?.videoUrl;
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
            setShowCategories(false);
            // console.log(playerInfo);
            // console.log(video.video);
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

    const saveToBookmarks = (id, category, type) => {
        if (type && category && type === 'video') {
            const url = `https://www.youtube.com/watch?v=${id}`;
            const newBm = { url, category: category };
            addBookmark(newBm);
            setShowInfoModal(true);
        } else if (type && category && type === 'playlist') {
            if (id && category) addPlaylistToBookmarks(id, category);
            setShowInfoModal(true);
        }
        setShowCategories(false);
        const show_modal = setTimeout(() => {
            setShowInfoModal(false);
            setSaveToCategory(null);
            setChangeActiveCategory(true);
        }, 5000);
        return () => {
            clearTimeout(show_modal);
        };
    };

    const handleGoToYouTube = (id, url) => {
        const go_to_url = `${url}${id}`;
        const newWindow = window.open(
            go_to_url,
            '_blank',
            'noopener',
            'noreferrer'
        );
        if (newWindow) newWindow.opener = null;
    };

    const handleCategoriesModal = (id, type) => {
        setShowCategories(true);
        setActiveId(id);
        setBookmarkType(type);
    };

    const related_videos_btn_click = (e) => {
        e.currentTarget.classList.toggle('active');
        if (e.target.id && activeId) {
            if (e.target.id !== activeId) {
                setShowCategories(false);
            }
        }
    };

    useEffect(() => {
        if (vp?.player) vp?.player?.setSize(newwidth, newwidth * 0.6);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [newsize, newwidth, vp?.player]);

    useEffect(() => {
        if (auth.isAuthenticated && auth.user.categories) {
            setCategories(auth.user.categories);
        } else {
            setCategories([]);
        }
    }, [auth]);

    useEffect(() => {
        if (auth.isAuthenticated) {
            if (data.bm) {
                const cat = data.bm.find(
                    (item) => item.category === data.activeCategory
                );
                if (cat) {
                    setIsEmptyCategory(false);
                } else {
                    if (categories.length > 1) {
                        setIsEmptyCategory(true);
                    } else setIsEmptyCategory(false);
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data.activeCategory, auth.isAuthenticated, categories, data.bm]);

    return (
        <StateContext.Provider
            value={{
                addCategoryModal,
                setAddCategoryModal,
                isEmptyCategory,
                setIsEmptyCategory,
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
                categoriesModalSelected,
                setCategoriesModalSelected,
                showCategories,
                setShowCategories,
                activeId,
                setActiveId,
                showInfoModal,
                setShowInfoModal,
                saveToBookmarks,
                categories,
                setCategories,
                handleGoToYouTube,
                handleCategoriesModal,
                bookmarkType,
                related_videos_btn_click,
                saveToCategory,
                setSaveToCategory,
                changeActiveCategory,
                setChangeActiveCategory,
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
    auth: state.auth,
    data: state.bm,
});

export default connect(mapStateToProps, {
    closeVideo,
    clearVideo,
    clearList,
    clearPlayer,
    addPlaylistToBookmarks,
    addBookmark,
})(ContextProvider);

export const useStateContext = () => useContext(StateContext);
