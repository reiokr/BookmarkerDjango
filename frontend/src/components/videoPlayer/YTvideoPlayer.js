import { useState, useEffect, useCallback, useRef } from 'react';
import '../../css/YTvideoPlayer.css';
import { connect } from 'react-redux';
import { loadPlayer } from '../../actions/playerActions';
import Player from './Player';
// import ChannelPlaylists from './ChannelPlaylists';
// import RelatedVideos from './RelatedVideos';
import PropTypes from 'prop-types';

const YTvideoPlayer = ({ video, auth, vp, loadPlayer }) => {
    // set initial state
    const [videoData] = useState({
        videoid: video?.video?.video_id,
        start_at: video?.video?.start_at ? video?.video?.start_at.toFixed() : 1,
        videoindex: video?.video?.list_index,
        listid: video?.video?.list_id,
    });

    const [playerWidth, setPlayerWidth] = useState(
        localStorage.getItem('ytpw')
    );
    const [playerVolume, setPlayerVolume] = useState(
        localStorage.getItem('playerVolume')
    );
    const wrapRef = useRef();
    const contRef = useRef();
    // const playerWidth = localStorage.getItem('ytpw') || 840;

    // create player object
    const loadVideoPlayer = useCallback(() => {
        if (!playerWidth) {
            localStorage.setItem('ytpw', 840);
            setPlayerWidth((prev) => localStorage.getItem('ytpw'));
        }
        if (!playerVolume) {
            localStorage.setItem('playerVolume', 50);
            setPlayerVolume((prev) => localStorage.getItem('playerVolume'));
        }

        // the Player object is created uniquely based on the id in state

        const player = new window.YT.Player(`player`, {
            videoId: videoData?.videoid,
            width: playerWidth,
            height: playerWidth * 0.6,
            playerVars: {
                enablejsapi: 1,
                autoplay: 1,
                loop: 0,
                controls: 1,
                showinfo: 1,
                autohide: 0,
                modestbranding: 1,
                fs: 1,
                cc_load_policy: 0,
                iv_load_policy: 3,
                start: videoData?.start_at,
                origin: 'http://localhost:3000',
            },
            events: {
                onReady: onPlayerReady,
                onStateChange: onPlayerStateChange,
            },
        });
        if (player && playerWidth && playerVolume) {
            loadPlayer(player);
            
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [videoData.videoid]);

    // get iframe api
    useEffect(() => {
        // check to see if the API script is already loaded
        if (!window.YT) {
            // If not, load the script asynchronously
            const tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            // onYouTubeIframeAPIReady will load the video after the script is loaded
            window.onYouTubeIframeAPIReady = loadVideoPlayer;
            const firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
            // If script is already there, load the video directly
        } else {
            loadVideoPlayer();
        }
    }, [loadVideoPlayer, videoData]);

    // if player state changes start the script
    const onPlayerStateChange = (event) => {
        // if video info changed load new player
        if (event?.target?.playerInfo) loadPlayer(event.target);
        // if user loged out stop player
        if (!auth.isAuthenticated) event.target.stopVideo();
    };

    // if player is ready start the video or playlist
    const onPlayerReady = (event) => {
        event.target.setVolume(Number(localStorage.getItem('playerVolume')));
        if (videoData.listid !== null) {
            event.target.loadPlaylist({
                listType: 'playlist',
                list: videoData.listid,
                index: Number(videoData.videoindex),
                startSeconds: Number(videoData.start_at),
            });
        } else {
            event.target.playVideo();
        }
    };

    return (
        <div className="container-player" ref={contRef}>
            <div id="wrap-player" ref={wrapRef}>
                <div className="video" id="video-container">
                    {auth.isAuthenticated && <Player ytvideo={video.video} />}
                </div>
            </div>
            {/* <ChannelPlaylists /> */}
            {/* <RelatedVideos /> */}
        </div>
    );
};
const mapStateToProps = (state) => ({
    auth: state.auth,
    video: state.ytv,
    vp: state.player,
});
YTvideoPlayer.propTypes = {
    auth: PropTypes.object.isRequired,
    video: PropTypes.object.isRequired,
    loadPlayer: PropTypes.func.isRequired,
};
export default connect(mapStateToProps, {
    loadPlayer,
})(YTvideoPlayer);
