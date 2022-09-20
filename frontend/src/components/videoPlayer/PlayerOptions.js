import { useEffect } from 'react';
import { connect } from 'react-redux';
import { MdSkipNext, MdSkipPrevious } from 'react-icons/md';
import { useTranslation } from 'react-i18next';
import { useToHHMMSS } from './script/timeConverter';
import { useStateContext } from '../../context/ContextProvider';

const PlayerOptions = ({
    closeCurrentVideo,
    video,
    vp,
    currIndex,
    isLastIndex,
}) => {
    const {
        btnRef,
        timestampControl,
        previousTimestamp,
        setPreviousTimestamp,
    } = useStateContext();
    const { t } = useTranslation();
    const prevTime = useToHHMMSS(previousTimestamp);

    const handleTimestampControl = () => {
        setPreviousTimestamp(
            (prev) => (prev = Number(vp?.player?.playerInfo?.currentTime))
        );
        const timeString = prevTime;
        let start_at = timeString
            .split(':')
            .reduce((acc, time) => 60 * acc + +time);
        if (start_at === 0) {
            start_at = 1;
        }
        vp?.player && vp?.player?.seekTo(start_at, true);
    };
    // console.log(video)
    // console.log(video?.video?.list_index)
    // console.log(vp?.player?.playerInfo?.playlist?.length);
    // console.log(isLastIndex());

    useEffect(() => {
        if (
            !video?.video?.list_index &&
            vp?.player?.playerInfo?.playlist?.length > 0
        ) {
            video.video.list_index = 0;
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [video?.video?.list_index, vp?.player?.playerInfo?.playlist]);

    return (
        <div className="video-player-options video" ref={btnRef}>
            <button
                data-text={t('Close video & save position')}
                type="button"
                id="close_bookmark"
                className="close-bookmark btn"
                onClick={closeCurrentVideo}
            >
                {t('Close')}
            </button>
            {timestampControl && (
                <div className="timestamp-control">
                    <button
                        className="timestamp-previous"
                        onClick={handleTimestampControl}
                    >
                        {t('previous timestamp')}
                        <span>{prevTime}</span>
                    </button>
                    {/* <span onClick={()=>{
                      setPreviousTimestamp(null)
                      setTimestampControl(false)}}>{t('close')}</span> */}
                </div>
            )}
            <div className="action-buttons">
                <button
                    className={`nextandprevious btn ${
                        (currIndex === 0) |
                            (vp?.player?.playerInfo?.playlist?.length === 0) |
                            (video?.video?.list_index === 0) |
                            (video?.video?.list_index === null) &&
                        'disable-button'
                    }`}
                    id="prev-video"
                    type="button"
                    onClick={() => {
                        vp?.player?.previousVideo();
                    }}
                >
                    <MdSkipPrevious className="icon" />
                </button>

                <button
                    className={`nextandprevious btn ${
                        (vp?.player?.playerInfo?.playlist?.length === 0) |
                            isLastIndex() |
                            (vp?.player?.playerInfo?.playlist?.length - 1 ===
                                video?.video?.list_index) |
                            (video?.video?.list_index === null) &&
                        'disable-button'
                    }`}
                    id="next-video"
                    type="button"
                    onClick={() => {
                        vp?.player?.nextVideo();
                    }}
                >
                    <MdSkipNext className="icon" />
                </button>
            </div>
        </div>
    );
};

const mapStateToProps = (state) => ({
    video: state.ytv,
    vp: state.player,
});

export default connect(mapStateToProps)(PlayerOptions);
