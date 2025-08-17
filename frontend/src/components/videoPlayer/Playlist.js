import { useState, useEffect, useCallback } from 'react';
import '../../css/Description.css';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { updateVideo } from '../../actions/ytvActions';
import moment from 'moment';
import img from '../../default-img.gif';
import { useStateContext } from '../../context/ContextProvider';
import LdsFacebook from '../LdsFacebook';

const Playlist = ({
    video,
    vp,
    setCurrIndex,
    updateVideo,
    currCategory,
    pl,
}) => {
    const { showlist } = useStateContext();
    const [playlist, setPlaylist] = useState(pl?.items);
    const [videoid] = useState(video.video.id);
    const reverseList = () => {
        const reversed = playlist?.reverse();
        setPlaylist(reversed);
        //  console.log(video.list);

    };
    useEffect(() => {
        if (video?.list !== null) {
            setPlaylist(video.list.items);
        }
    }, [video.list, reverseList]);

    const handleListItem = (index) => {
        if (vp?.player.playVideoAt && index) {
            // using youtube api player object start video at index
            const newVideo = vp?.player?.playVideoAt(Number(index));
            if (newVideo) updateVideoData();
        }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps



    const updateVideoData = useCallback(() => {
        // update database
        const data = {
            video_id: vp?.player?.playerInfo?.videoData?.video_id,
            list_id: vp?.player?.playerInfo?.playlistId,
            list_index: vp?.player?.playerInfo?.playlistIndex,
            start_at: 0,
            category: currCategory,
            url:
                'https://youtu.be/' +
                vp?.player?.playerInfo?.videoData?.video_id,
        };
        if (
            videoid &&
            vp?.player?.playerInfo?.videoData?.video_id &&
            currCategory
        )
            updateVideo(videoid, data, currCategory);
    }, [
        currCategory,
        updateVideo,
        videoid,
        vp?.player?.playerInfo?.playlistId,
        vp?.player?.playerInfo?.playlistIndex,
        vp?.player?.playerInfo?.videoData?.video_id,
    ]);


    return (
        <>
            {video.list === null && showlist && <LdsFacebook />}
            {showlist && video.list !== null ? (
                <div className="playlist playlist-visible">
                    <button className='reverse-list btn' onClick={reverseList}>Reverse List</button>
                    {playlist !== null &&
                        showlist &&
                        vp?.player?.playerInfo &&
                        playlist?.map((item, index) => {
                            return (
                                <li
                                    className={`${
                                        vp?.player?.playerInfo
                                            ?.playlistIndex === index
                                            ? 'li-active'
                                            : ''
                                    } ${
                                        item.title === 'Private video'
                                            ? 'private-video'
                                            : ''
                                    }`}
                                    key={index}
                                    onClick={() => {
                                        if (item.title === 'Private video') {
                                            
                                        } else {
                                            handleListItem(item.list_index);
                                            setCurrIndex(item.list_index);
                                        }
                                    }}
                                >
                                  {/* <div className="playlist-item-description">{item.description}</div> */}
                                    <img
                                        src={
                                            item.title === 'Private video'
                                                ? img
                                                : item.thumbnails?.medium?.url
                                        }
                                        alt={item.title}
                                    />
                                    <p>
                                        Published:{' '}
                                        {moment(item.published_at).format('LL')}
                                    </p>
                                    <p>{item.title}</p>
                                </li>
                            );
                        })}
                </div>
            ) : null}
        </>
    );
};

const mapStateToProps = (state) => ({
    video: state.ytv,
    vp: state.player,
    currCategory: state.bm.activeCategory,
});

Playlist.propTypes = {
    video: PropTypes.object.isRequired,
    vp: PropTypes.object.isRequired,
};

export default connect(mapStateToProps, { updateVideo })(Playlist);
