// convert seconds to hh:mm:ss
var useToHHMMSS = (secs) => {
    var sec_num = parseInt(secs, 10)
    var hours = Math.floor(sec_num / 3600)
    var minutes = Math.floor(sec_num / 60) % 60
    var seconds = sec_num % 60
    return [hours || '0', minutes || '0', seconds || '0']
        .map((v) => (v < 10 ? '0' + v : v))
        .filter((v, i) => v !== '00' || i > 0)
        .join(':')
}

const useSecondsTo_HHMMSS = (seconds) => {
    //format to a readable friendly timer
    let hour = Math.floor(seconds / 3600)
    let minute = Math.floor((seconds % 3600) / 60)
    let second = seconds % 60
    if (hour.toString().length === 1) {
        hour = `0${hour}`
    }
    if (minute.toString().length === 1) {
        minute = `0${minute}`
    }
    if (second.toString().length === 1) {
        second = `0${second}`
    }
    let timer = `${hour}:${minute}:${second}`

    return timer
}

export { useToHHMMSS, useSecondsTo_HHMMSS }
