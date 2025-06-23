import { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import {
    loadChannelPlaylists,
    loadMoreChannelPlaylists,
} from '../../actions/playerActions';
import { addPlaylistToBookmarks } from '../../actions/bmActions';
import InfoModal from '../../components/InfoModal';
import moment from 'moment';
import CategoriesModal from './CategoriesModal';
import { useStateContext } from '../../context/ContextProvider';

const ChannelPlaylists = ({
    vp,
    video,
    loadChannelPlaylists,
    loadMoreChannelPlaylists,
}) => {
    const {
        showCategories,
        activeId,
        setActiveId,
        showInfoModal,
        handleGoToYouTube,
        handleCategoriesModal,
        bookmarkType,
        related_videos_btn_click,
    } = useStateContext();
    const [channelPlaylists, setChannelPlaylists] = useState(null);

    useEffect(() => {
        if (!vp?.channel_playlists) {
            video?.video?.channel_id &&
                loadChannelPlaylists(video?.video?.channel_id);
        } else {
            if (vp?.channel_playlists?.items?.length > 0) {
                if (
                    video?.video?.channel_id !==
                    vp?.channel_playlists?.items[0]?.snippet?.channelId
                ) {
                    video?.video?.channel_id &&
                        loadChannelPlaylists(video?.video?.channel_id);
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [video?.video?.channel_id]);

    useEffect(() => {
        if (vp?.channel_playlists?.items?.length > 0) {
            setChannelPlaylists(vp.channel_playlists);
        }
    }, [vp?.channel_playlists]);

    const handleLoadMorePlaylists = () => {
        channelPlaylists?.nextPageToken &&
            loadMoreChannelPlaylists(
                video.video.channel_id,
                channelPlaylists.nextPageToken
            );
    };

    return (
        <>
            {showInfoModal && bookmarkType === 'playlist' && (
                <InfoModal content={'Playlist saved to '} />
            )}
            {vp?.channel_playlists?.items?.length > 0 && (
                <div className="channel-playlists">
                    <h4>Playlists in {video.video.channel_title} channel</h4>
                    <div className="channel-playlists-body">
                        {channelPlaylists?.items &&
                            channelPlaylists.items.map((playlist) => {
                                return (
                                    playlist.contentDetails.itemCount !== 0 && (
                                        <div
                                            key={playlist.id}
                                            className="ch-pl-container"
                                        >
                                            {showCategories &&
                                                activeId === playlist.id && (
                                                    <CategoriesModal />
                                                )}
                                            <div
                                                className="ch-pl-image-container"
                                                // data-text={tooltipText}
                                            >
                                                <div
                                                    className="related-videos-btn"
                                                    id={playlist.id}
                                                    onClick={
                                                        related_videos_btn_click
                                                    }
                                                    onMouseLeave={(e) => {
                                                        e.target.classList.remove(
                                                            'active'
                                                        );
                                                    }}
                                                >
                                                    <span id="h">
                                                        <p
                                                            className="icon"
                                                            onClick={() => {
                                                                handleCategoriesModal(
                                                                    playlist.id,
                                                                    'playlist'
                                                                );
                                                            }}
                                                        >
                                                            Bookmark
                                                        </p>
                                                    </span>
                                                    <span id="e">
                                                        <p
                                                            className="icon"
                                                            onClick={() => {
                                                                setActiveId(
                                                                    null
                                                                );
                                                                handleGoToYouTube(
                                                                    playlist.id,
                                                                    'https://www.youtube.com/playlist?list='
                                                                );
                                                            }}
                                                        >
                                                            YouTube
                                                        </p>
                                                    </span>
                                                    <span
                                                        id="o"
                                                        onClick={() => {
                                                            setActiveId(null);
                                                        }}
                                                    >
                                                        <p className="icon">
                                                            Play
                                                        </p>
                                                    </span>
                                                </div>
                                                <img
                                                    src={
                                                        playlist.snippet
                                                            .thumbnails?.medium
                                                            ?.url
                                                    }
                                                    alt={''}
                                                />
                                            </div>
                                            <div className="ch-pl-body">
                                                <p className="ch-pl-title">
                                                    {playlist.snippet.title}
                                                </p>
                                                <div className="ch-pl-footer">
                                                    <span className="ch-pl-published">
                                                        {moment(
                                                            playlist.snippet
                                                                .publishedAt
                                                        ).format('MMM Do YYYY')}
                                                    </span>
                                                    <span className="ch-pl-count">
                                                        {
                                                            playlist
                                                                .contentDetails
                                                                .itemCount
                                                        }
                                                        {playlist.contentDetails
                                                            .itemCount === 1
                                                            ? ' video'
                                                            : ' videos'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                );
                            })}
                        {channelPlaylists?.nextPageToken && (
                            <h4
                                className="ch-pl-load-more"
                                onClick={handleLoadMorePlaylists}
                            >
                                Load more...
                            </h4>
                        )}
                    </div>
                </div>
            )}
        </>
    );
};

const mapStateToProps = (state) => ({
    vp: state.player,
    video: state.ytv,
    currCategory: state.bm.activeCategory,
});

export default connect(mapStateToProps, {
    loadChannelPlaylists,
    loadMoreChannelPlaylists,
    addPlaylistToBookmarks,
})(ChannelPlaylists);
