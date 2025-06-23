import { useEffect, useState, useCallback } from 'react';
import { connect } from 'react-redux';
import parse from 'html-react-parser';
import linkifyHtml from 'linkify-html';
import { updateVideo } from '../../actions/ytvActions';
import { clearVideoData } from '../../actions/bmActions';
import moment from 'moment';
import { MdOutlinePreview } from 'react-icons/md';
import { AiOutlineComment, AiOutlineLike } from 'react-icons/ai';
import { ImYoutube2 } from 'react-icons/im';
import { GiDuration } from 'react-icons/gi';
import { useTranslation } from 'react-i18next';
import { useStateContext } from '../../context/ContextProvider';
import LdsFacebook from '../LdsFacebook';

const FormatText = ({
    videoData,
    videoInfo,
    video_length,
    currCategory,
    updateVideo,
    clearVideoData,
    description,
    noloader,
    video,
    vp,
}) => {
    const {
        setTimestampControl,
        timestampPreviousTime,
        showdesc,
        setTimestampClicked,
    } = useStateContext();
    const [desc, setDesc] = useState('');
    const [currDesc, setCurrDesc] = useState(description);
    const { t } = useTranslation();

    useEffect(() => {

        if (video?.video?.description && !noloader) {
          setCurrDesc(video.video.description);
        }
      
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [video?.video?.description]);

    const handleTimestampPrevTime = useCallback(() => {
        timestampPreviousTime(Number(vp?.player?.playerInfo?.currentTime));
        setTimestampControl(true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [timestampPreviousTime, vp?.player?.playerInfo?.currentTime]);

    const playVideoAtTimestamp = useCallback(
        (start_at) => {
            handleTimestampPrevTime();
            if (start_at === 0) start_at = 0.1;
            // update database
            if (videoData?.video_id) {
                const data = {
                    video_id: videoData?.video_id,
                    list_id: videoData?.list_id || null,
                    list_index: videoData?.list_index || null,
                    start_at: start_at,
                    category: currCategory,
                    url: 'https://youtu.be/' + videoData?.video_id,
                };
                if (videoData) {
                    updateVideo(videoData?.id, data, currCategory);
                    clearVideoData();
                }
            }

            vp?.player?.seekTo(start_at, true);
        },
        [
            clearVideoData,
            currCategory,
            handleTimestampPrevTime,
            updateVideo,
            videoData,
            vp?.player,
        ]
    );

    useEffect(() => {
        let modal = document.querySelector('#root');
        // if (modal === null) {
        //     modal = document.querySelector('body')
        // }
        // console.log('modal')
        modal.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }, [vp]);

    useEffect(() => {
        const timestamps = document.querySelectorAll('.timestamp');
        timestamps.forEach((timestamp) => {
            timestamp.addEventListener('click', (e) => {
                const timeString = e.target.textContent;
                let start_at = timeString
                    .split(':')
                    .reduce((acc, time) => 60 * acc + +time);
                playVideoAtTimestamp(start_at);
                setTimestampClicked(true);
            });
        });
    });
    const options = {
        attributes: null,
        className: null,
        defaultProtocol: 'http',
        events: null,
        format: (value, type) => value,
        formatHref: (href, type) => href,
        ignoreTags: [],
        nl2br: true,
        rel: null,
        tagName: 'a',
        target: null,
        truncate: 42,
        validate: true,
    };

    const findAndReplace = () => {
        const regex = /(?:\d?\d:\d\d:?\d?\d?)/gm;

        if (currDesc) {
            const newstr = currDesc.replace(
                regex,
                `<a class="timestamp" href="#">$&</a>`
            );
            const result = linkifyHtml(newstr, options);
            setDesc(result);
        }
    };

    useEffect(() => {
        findAndReplace();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currDesc]);

    return (
        <>
            {!desc && showdesc && !noloader && <LdsFacebook />}

            {videoInfo && (
                <div className="video-info">
                    <span
                        className="video-info-text"
                        data-text={t('Channel link')}
                    >
                        <span>
                            <a
                                href={`https://www.youtube.com/channel/${videoInfo?.channel_id}`}
                                target="_blank"
                                rel="noreferrer"
                            >
                                {videoInfo?.channel_title}
                            </a>
                        </span>
                    </span>
                    <span
                        className="video-info-text"
                        data-text={t('Published')}
                    >
                        <span>
                            {moment(videoInfo?.publish_date).format(
                                'MMM Do YYYY'
                            )}
                        </span>
                    </span>
                    <span className="video-info-text" data-text={t('Duration')}>
                        <GiDuration />
                        <span> {video_length}</span>
                    </span>
                    <span className="video-info-text" data-text={t('Likes')}>
                        <AiOutlineLike />
                        <span> {videoInfo?.like_count}</span>
                    </span>
                    <span className="video-info-text" data-text={t('Comments')}>
                        <AiOutlineComment />
                        <span> {videoInfo?.comment_count}</span>
                    </span>
                    <span className="video-info-text" data-text={t('Views')}>
                        <MdOutlinePreview />
                        <span> {videoInfo?.view_count}</span>
                    </span>
                    {videoInfo.bm_type === 'yt' && (
                        <div className="descmodal-link">
                            {/* <span>{t('Go to')}</span> */}
                            <a
                                href={videoInfo.url}
                                target="_blank"
                                rel="noreferrer"
                            >
                                <ImYoutube2 className="youtube-icon" />
                            </a>
                        </div>
                    )}
                </div>
            )}

            <div id="formatted-description">{parse(desc)}</div>
        </>
    );
};

const mapStateToProps = (state) => ({
    videoData: state.bm.videoData,
    video: state.ytv,
    vp: state.player,
    currCategory: state.bm.activeCategory,
});

export default connect(mapStateToProps, { updateVideo, clearVideoData })(
    FormatText
);
