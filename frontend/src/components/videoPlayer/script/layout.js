// video player //
//////////////////
const currentW = localStorage.getItem('ytpw') || 3
const slider = document.getElementById('player-width')
slider.value = currentW
var timeOutFunctionId


// calculate optimal value
const calcW = 10 / Number(currentW)

const width = window.screen.width / calcW
const wrapperPadding = 10
const resizeVideo = document.getElementById('resize-video')
const options = document.querySelector('.video-player-options')
const options_two = document.querySelector('.video-player-options-two')
const videoWrapper = document.getElementById('wrap-player')
const playListShow = document.querySelector('.playlist-container')
let root = document.documentElement
root.style.setProperty('--video-width', width + 'px')
if (!options) {
} else {
  options.style.width = width + 'px'
  options_two.style.width = width + 'px'
  playListShow.style.width = width + 'px'
}
if (
  /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  )
) {
  options_two.style.display = 'none'
}

window.onload = () => {
  if (
    window.innerWidth < width ||
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    )
  ) {
    const videoContainer = document.getElementById('video-container')
    const videoPlayer = document.getElementById('player')
    videoContainer.classList.toggle('video-container')
    videoPlayer.classList.toggle('video-player')
    resizeVideo.style.display = 'none'
    options.style.width = '100%'
    options_two.style.width = '100%'
    playListShow.style.width = '100%'
    videoWrapper.style.paddingLeft = '0'
    videoWrapper.style.paddingRight = '0'
  }
}

resizeVideo.addEventListener('click', (e) => {
  e.preventDefault()
  const videoContainer = document.getElementById('video-container')
  const videoPlayer = document.getElementById('player')
  videoContainer.classList.toggle('video-container')
  videoPlayer.classList.toggle('video-player')
  videoPlayer.classList.remove('partial-responsive')

  if (videoPlayer.classList.contains('video-player')) {
    videoPlayer.classList.add('responsive')
    resizeVideo.textContent = 'Small player'
    resizeVideo.setAttribute('title', 'Watch video in small window')
    options.style.width = '100%'
    options_two.style.display = 'none'
    playListShow.style.width = '100%'
    videoWrapper.style.paddingLeft = '0'
    videoWrapper.style.paddingRight = '0'
    videoWrapper.style.paddingTop = '0'
    videoWrapper.style.maxWidth = '150vh'
  } else {
    videoPlayer.classList.remove('responsive')
    resizeVideo.textContent = 'Cinema mode'
    resizeVideo.setAttribute('title', 'Watch video in Cinema mode')
    options.style.width = width + 'px'
    options_two.style.display = 'flex'
    options_two.style.width = width + 'px'
    playListShow.style.width = width + 'px'
    options.style.height = '50px!important'
    options_two.style.height = '50px!important'
    videoWrapper.style.padding = wrapperPadding + 'px'
    videoWrapper.style.maxWidth = '100%'
  }
})

const widthOutput = document.querySelector('#width')
function reportWindowSize() {
  widthOutput.textContent = window.innerWidth
  const videoContainer = document.getElementById('video-container')
  const videoPlayer = document.getElementById('player')
  if (Number(widthOutput.textContent) < width + wrapperPadding * 2) {
    resizeVideo.style.display = 'none'
  }
  if (Number(widthOutput.textContent) >= width + wrapperPadding * 2) {
    resizeVideo.style.display = 'inline-block'
  }
  if (videoPlayer.classList.contains('responsive')) {
    return
  }
  if (Number(widthOutput.textContent) < width + wrapperPadding * 2) {
    videoPlayer.classList.add('partial-responsive')
    videoContainer.classList.add('video-container')
    videoPlayer.classList.add('video-player')
    resizeVideo.style.display = 'none'
    options.style.width = '100%'
    options_two.style.width = '100%'
    playListShow.style.width = '100%'
    options.style.height = '50px!important'
    options_two.style.height = '50px!important'
    videoWrapper.style.paddingLeft = '0'
    videoWrapper.style.paddingRight = '0'
    videoWrapper.style.maxWidth = '100%'
  }
  if (
    Number(widthOutput.textContent) >= width + wrapperPadding * 2 &&
    videoPlayer.classList.contains('partial-responsive')
  ) {
    videoContainer.classList.remove('video-container')
    videoPlayer.classList.remove('video-player')
    options.style.width = width + 'px'
    options_two.style.width = width + 'px'
    playListShow.style.width = width + 'px'
    videoWrapper.style.padding = wrapperPadding + 'px'
    videoWrapper.style.maxWidth = '100%'
    resizeVideo.style.display = 'inline-block'
  }
}

window.onresize = reportWindowSize
window.addEventListener('resize', reportWindowSize)

