import { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import {
    loadChannelPlaylists,
    loadMoreChannelPlaylists,
} from '../../actions/playerActions';
import { addPlaylistToBookmarks } from '../../actions/bmActions';
import InfoModal from '../../components/InfoModal';
import moment from 'moment';

const ChannelPlaylists = ({
    vp,
    video,
    loadChannelPlaylists,
    loadMoreChannelPlaylists,
    addPlaylistToBookmarks,
    currCategory,
}) => {
    const [channelPlaylists, setChannelPlaylists] = useState(null);
    const tooltipText = 'Save to bookmarks?';
    const [showInfoModal, setShowInfoModal] = useState(false);

    useEffect(() => {
      if (!vp?.channel_playlists) {
          video?.video?.channel_id &&
              loadChannelPlaylists(video?.video?.channel_id);
      } else {
          if (
              video.video.channel_id !==
              vp.channel_playlists.items[0].snippet.channelId
          ) {
              video?.video?.channel_id &&
                  loadChannelPlaylists(video?.video?.channel_id);
          }
      }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [video.video.channel_id]);

    useEffect(() => {
        if (vp?.channel_playlists) {
            setChannelPlaylists(vp.channel_playlists);
        }
    }, [vp.channel_playlists]);
    // console.log(vp.channel_playlists.items[0].snippet.channelId)
    // console.log(video.video.channel_id)
    const handleSavePlaylistToBookmarks = (pl_id) => {
        addPlaylistToBookmarks(pl_id, currCategory);
        setShowInfoModal(true);
        const show_modal = setTimeout(() => {
            setShowInfoModal(false);
        }, 3000);
        return () => {
            clearTimeout(show_modal);
        };
        // closeCurrentVideo();
    };

    const handleLoadMorePlaylists = () => {
        channelPlaylists?.nextPageToken &&
            loadMoreChannelPlaylists(
                video.video.channel_id,
                channelPlaylists.nextPageToken
            );
    };

    // console.log(channelPlaylists);
    return (
        <>
            {showInfoModal && (
                <InfoModal content={'Playlist saved to bookmarks'} />
            )}
            <div className="channel-playlists">
                <h4>Playlists in {video.video.channel_title} channel</h4>
                {channelPlaylists?.items &&
                    channelPlaylists.items.map((playlist) => {
                        // console.log(playlist);
                        return (
                            playlist.contentDetails.itemCount !== 0 && (
                                <div
                                    key={playlist.id}
                                    className="ch-pl-container"
                                >
                                    <div
                                        className="ch-pl-image-container"
                                        data-text={tooltipText}
                                        onClick={() => {
                                            handleSavePlaylistToBookmarks(
                                                playlist.id
                                            );
                                        }}
                                    >
                                        <p className="ch-pl-count">
                                            {playlist.contentDetails.itemCount}
                                            {playlist.contentDetails
                                                .itemCount === 1
                                                ? ' video'
                                                : ' videos'}
                                        </p>
                                        <img
                                            src={
                                                playlist.snippet.thumbnails
                                                    ?.medium?.url
                                            }
                                            alt={''}
                                        />
                                    </div>
                                    <div className="ch-pl-body">
                                        <p className="ch-pl-title">
                                            {playlist.snippet.title}
                                        </p>
                                        <p className="ch-pl-published">
                                            Published:{' '}
                                            {moment(
                                                playlist.snippet.publishedAt
                                            ).format('MMM Do YYYY')}
                                        </p>
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
                <div className="ch-pl-padding"></div>
            </div>
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
