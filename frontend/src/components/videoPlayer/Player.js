import { useState, useRef, useEffect } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { clearPlayer } from '../../actions/playerActions';
import Description from './Description';
import Playlist from './Playlist';
import TimestampModal from './TimestampModal';
import CommentModal from './CommentModal';
import { getVideo, clearVideoData, rateVideo } from '../../actions/bmActions';
import {
    load_video_comments,
    clear_comments,
    load_next_comments,
} from '../../actions/commentsActions';
import PlayerOptions from './PlayerOptions';
import PlayerButtons from './PlayerButtons';
import moment from 'moment';
import { useSecondsTo_HHMMSS } from './script/timeConverter';
import {
    closeVideo,
    clearVideo,
    clearList,
    getList,
    updateVideo,
    saveVideoInterval,
} from '../../actions/ytvActions';
import { useStateContext } from '../../context/ContextProvider';

const Player = ({
    video,
    vp,
    currCategory,
    getList,
    updateVideo,
    ytvideo,
    load_video_comments,
    comments,
    load_next_comments,
    saveVideoInterval,
    clear_comments,
}) => {
    const {
        commentOrder,
        showComments,
        setPreviousTimestamp,
        isLastComment,
        setIsLastComment,
        btnRef,
        newwidth,
        showlist,
        setShowlist,
        timestampClicked,
        setTimestampClicked,
        closeCurrentVideo,
    } = useStateContext();

    const vpId = vp?.player?.playerInfo?.videoData?.video_id;
    const vId = video?.video?.id;
    const playerInfo = vp?.player?.playerInfo;
    const [currIndex, setCurrIndex] = useState(video.video.list_index);
    const [description, setDescription] = useState(video?.video?.description);
    const [isPlayerLoaded, setIsPlayerLoaded] = useState(false);
    const [currTime, setCurrTime] = useState(Number(playerInfo?.currentTime));
    const [currVideoId, setCurrVideoId] = useState(null);
    const video_length = useSecondsTo_HHMMSS(
        moment.duration(video.video.length).asSeconds()
    );
    const contRef = useRef();
    const playerRef = useRef();

    const updateVideoData = () => {
        // update bookmark in database
        if (vpId) {
            let curr_time;
            try {
                curr_time = Number(vp?.player?.getCurrentTime());
            } catch (error) {
                return;
            }
            const data = {
                video_id: vpId,
                list_id: playerInfo?.playlistId,
                list_index: playerInfo?.playlistIndex,
                list_items_count: playerInfo?.playlist?.length || 0,
                start_at: curr_time,
                category: currCategory,
                url: 'https://youtu.be/' + video.video_id,
            };
            if (ytvideo.video_id !== vpId) {
                setShowlist(false);
                updateVideo(vId, data, currCategory);
                setCurrIndex(playerInfo?.playlistIndex);
                setDescription(video.video.description);
                setPreviousTimestamp(null);
            }
        }
    };

    const saveVideo = (start_at) => {
        if (start_at && vp?.player?.playerInfo) {
            video.video.start_at = start_at;

            video.video.list_items_count =
                vp?.player?.playerInfo?.playlist?.length || 0;
            video.video.video_id = vpId;

            const data = {
                video_data: video.video,
            };
            saveVideoInterval(vId, data);
        }
    };

    // check if last video in playlist
    const isLastIndex = () => {
        const playlist = video?.list?.items.filter(
            (item) => item.title !== 'Private video'
        );
        let lastIndex;
        if (playlist) {
            lastIndex = playlist[playlist?.length - 1].list_index;
        }
        if (currIndex === lastIndex) return true;
    };

    // check if scrolled to bottom of screen
    const isBottom = () => {
        const el = document.querySelector('.description-container-player');
        if (el) {
            const { scrollHeight } = document.querySelector(
                '.description-container-player'
            );
            const { scrollTop, clientHeight } = document.documentElement;
            const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
            return distanceFromBottom < -100;
        }
    };

    // if scrolled to bottom of screen set isLastComment true
    const handleEvent = () => {
        if (comments?.comments.length !== 0 && showComments) {
            isBottom() && setIsLastComment(true);
        }
    };

    useEffect(() => {
        setCurrVideoId((prev) => video.video.video_id);
    }, [video.video.video_id]);

    useEffect(() => {
        setShowlist(false);
        if (video?.video?.list_id !== video?.list?.id) {
            clearList();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // sets interval to save video play time
    useEffect(() => {
        const interval = setInterval(() => {
            if (currTime !== playerInfo?.currentTime) {
                setCurrTime((prev) => playerInfo?.currentTime);
                try {
                    saveVideo(vp?.player?.getCurrentTime());
                } catch (error) {}
            }
        }, 20000);
        return () => clearInterval(interval);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isPlayerLoaded]);

    // scroll to top of screen after clicking on timestamp
    useEffect(() => {
        let modal = document.querySelector('#root');
        timestampClicked &&
            modal.scrollIntoView({ block: 'start', behavior: 'smooth' });
        setTimestampClicked(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [timestampClicked]);

    // if video is in playlist load playlist items
    useEffect(() => {
        if (
            video?.video?.list_id &&
            !video?.list | (video?.video?.list_id !== video?.list?.id) &&
            showlist
        ) {
            getList(video?.video?.list_id);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [getList, video.video.list_id, showlist]);

    // control resizing video player and container
    useEffect(() => {
        btnRef.current.style.width = newwidth + 'px';
        contRef.current.style.width = newwidth + 'px';
    }, [btnRef, newwidth]);

    // if video id changes update bookmark in database and change video description and load comments
    useEffect(() => {
        if (vpId && currVideoId) {
            setIsPlayerLoaded(true);
            if (vpId !== currVideoId) {
                console.log(vpId);
                updateVideoData();
                setDescription(video.video.description);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [vpId]);

    useEffect(() => {
        if (vpId && showComments) {
            if (
                vpId === currVideoId &&
                showComments &&
                comments.comments.length === 0
            ) {
                load_video_comments(vpId, commentOrder);
            } else {
                if (
                    showComments &&
                    comments.comments.length > 0 &&
                    comments.comments[0].snippet.videoId !== currVideoId
                ) {
                    load_video_comments(vpId, commentOrder);
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [vpId, showComments, currVideoId, comments.comments]);

    // if changed order then load comments in new order
    useEffect(() => {
        showComments && load_video_comments(vpId, commentOrder);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [commentOrder]);

    // if nextPageToken in comments object then can load more comments
    useEffect(() => {
        comments.nextPageToken && setIsLastComment(false);
    }, [comments.nextPageToken, setIsLastComment]);

    // if scrolled down load next comments
    useEffect(() => {
        if (showComments && isLastComment && comments.nextPageToken) {
            load_next_comments(vpId, comments.nextPageToken, commentOrder);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLastComment, showComments]);

    // listen scrolling
    useEffect(() => {
        showComments
            ? window.addEventListener('scroll', handleEvent)
            : window.removeEventListener('scroll', handleEvent);
        return () => window.removeEventListener('scroll', handleEvent);
    });

    // if player volume changes save the value to local storage
    useEffect(() => {
        playerInfo?.volume &&
            playerInfo?.volume !== null &&
            localStorage.setItem('playerVolume', vp?.player?.getVolume());
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [playerInfo?.volume]);

    return (
        <>
            {video.video && (
                <div id="player" className="video-player" ref={playerRef}></div>
            )}
            {video.video && <TimestampModal description={description} />}
            <PlayerOptions
                currIndex={currIndex}
                isLastIndex={isLastIndex}
                closeCurrentVideo={closeCurrentVideo}
            />
            <div className="description-container-player" ref={contRef}>
                <PlayerButtons video_length={video_length} />
                <Description
                    description={description}
                    videoInfo={video.video}
                    video_length={video_length}
                />
                {video?.video?.list_id && (
                    <Playlist
                        currIndex={currIndex}
                        setCurrIndex={setCurrIndex}
                        pl={video.list}
                    />
                )}
                {comments.comments.length > 0 && showComments && (
                    <CommentModal />
                )}
            </div>
        </>
    );
};
const mapStateToProps = (state) => ({
    video: state.ytv,
    vp: state.player,
    currCategory: state.bm.activeCategory,
    comments: state.comments,
});

Player.propTypes = {
    video: PropTypes.object.isRequired,
    vp: PropTypes.object.isRequired,
    closeVideo: PropTypes.func.isRequired,
    clearVideo: PropTypes.func.isRequired,
    getList: PropTypes.func.isRequired,
    clearPlayer: PropTypes.func.isRequired,
    clearList: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, {
    clearPlayer,
    closeVideo,
    clearVideo,
    clearList,
    updateVideo,
    getList,
    getVideo,
    clearVideoData,
    load_video_comments,
    clear_comments,
    rateVideo,
    load_next_comments,
    saveVideoInterval,
})(Player);
