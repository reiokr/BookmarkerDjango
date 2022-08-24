import { useState, useEffect, useCallback, useRef } from 'react'
import { connect } from 'react-redux'
import parse from 'html-react-parser'
import { CgCloseO } from 'react-icons/cg'
import { FiMove } from 'react-icons/fi'
import Draggable from 'react-draggable'
import { useStateContext } from '../../context/ContextProvider'
const TimestampModal = ({ vp, video }) => {
    const {
        showtimestamps,
        setShowtimestamps,
        setTimestampBtn,
        setTimestampControl,
        timestampPreviousTime,
    } = useStateContext()
    
    const [timestamps, setTimestamps] = useState(null)
    const [currDesc, setCurrDesc] = useState(video?.video?.description)
    const nodeRef = useRef(null)
    const extractTimestamsFromDescription = useCallback(() => {
        const regex = /(?:\d?\d:\d\d:?\d?\d?)/gm
        const newstr = currDesc.replace(
            regex,
            `<a class="timestamp" href="#">$&</a>`
        )
        const re = /(?:.*\d?\d:\d\d:?\d?\d?.*)/gm
        const array = [...newstr.matchAll(re)]
        if (array.length < 1) {
            setTimestampBtn(false)
            setShowtimestamps(false)
        } else {
            setTimestampBtn(true)
        }
        let myArr = array.toString().replaceAll(',', '</br>')
        setTimestamps(myArr)
    }, [currDesc, setShowtimestamps, setTimestampBtn])

    useEffect(() => {
        if (currDesc) {
            extractTimestamsFromDescription()
        }
    }, [currDesc, extractTimestamsFromDescription])

    useEffect(() => {
        if (video?.video?.description) {
            setCurrDesc(video?.video?.description)
        }
    }, [video?.video?.description])

    useEffect(() => {
        const currTimestamps = document.querySelectorAll('.timestamp')
        currTimestamps.forEach((timestamp) => {
            timestamp.addEventListener('click', (e) => {
                setTimestampControl(true)
                timestampPreviousTime(
                    Number(vp?.player?.playerInfo?.currentTime)
                )
                const timeString = e.target.textContent
                let start_at = timeString
                    .split(':')
                    .reduce((acc, time) => 60 * acc + +time)
                if (start_at === 0) {
                    start_at = 0.1
                }
                vp?.player && vp?.player?.seekTo(start_at, true)
            })
        })
    })

    return (
        <>
            {showtimestamps && (
                <Draggable nodeRef={nodeRef}>
                    <div ref={nodeRef} className="timestamps-modal">
                        <span className="move-icon">
                            <FiMove />
                        </span>
                        <div className="close-btn-bm">
                            <CgCloseO
                                className="close-icon"
                                onClick={() => {
                                    setShowtimestamps(false)
                                }}
                            />
                        </div>
                        {parse(timestamps)}
                    </div>
                </Draggable>
            )}
        </>
    )
}
const mapStateToProps = (state) => ({
    vp: state.player,
    video: state.ytv,
})
export default connect(mapStateToProps)(TimestampModal)
