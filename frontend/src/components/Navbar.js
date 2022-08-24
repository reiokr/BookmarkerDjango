import '../css/Navbar.css'
import { useState } from 'react'
import { connect } from 'react-redux'
import { logout } from '../actions/authActions'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import Menu from './Menu'
import { clearPlayer } from '../actions/playerActions'
import { closeVideo, clearVideo, clearList } from '../actions/ytvActions'
import { useTranslation } from 'react-i18next'
import LocaleButton from './LocaleButton'

const Navbar = ({
    auth,
    logout,
    video,
    vp,
    currCategory,
    clearPlayer,
    closeVideo,
    clearVideo,
    clearList,
}) => {
    const { t } = useTranslation()
    const [active, setActive] = useState('/')
    const [show, setShow] = useState(false)
    const toggleMenu = () => setShow(!show)
    const categories_authlinks = [
        { text: t('nav_bookmarks'), link: '/' },
        // {text:t('nav_about'),link:"/about"},
        // {text:t('nav_contact'),link:"/contact}",
        { text: t('nav_user'), link: '/user' },
        { text: t('nav_logout'), link: '/logout' },
    ]
    const categories_guestlinks = [
        // {text:t('nav_about'),link:"/about"},
        // {text:t('nav_contact'),link:"/contact}",
        { text: t('nav_signup'), link: 'signup' },
        { text: t('nav_login'), link: 'login' },
    ]

    // if video player is active close video and update
    const closeCurrentVideo = () => {
        if (vp.player.playerInfo) {
            localStorage.setItem('playerVolume', vp?.player?.playerInfo?.volume)
            const startAt = Number(vp?.player?.playerInfo?.currentTime)
            const data = {
                video_data: video.video,
                start_at: startAt,
            }

            closeVideo(video.video.id, data, currCategory)
            clearVideo()
            clearPlayer()
            clearList()
        }
    }

    const authLinks = (
        <>
            {categories_authlinks &&
                categories_authlinks.map((link) => (
                    <Link
                        key={link.text}
                        to={link.link}
                        onClick={() => {
                            if (vp.isPlayerReady) closeCurrentVideo()
                            if (link.link === '/logout') logout()
                            setActive(link.link)
                        }}
                        className={`${active === link.link ? 'active' : ''}`}
                    >
                        {link.text}
                    </Link>
                ))}
        </>
    )

    const guestLinks = (
        <>
            {categories_guestlinks.map((link) => (
                <Link
                    key={link.text}
                    to={link.link}
                    onClick={() => {
                        setActive(link.link)
                    }}
                    className={`${active === link.link ? 'active' : ''}`}
                >
                    {link.text}
                </Link>
            ))}
        </>
    )

    return (
        <div className="header">
            <div className="navbar">
                <Link className="navbar-logo" to="/">
                    YTbookmarks
                </Link>
                <div className={show ? 'menu-list show' : 'menu-list'}>
                    {!auth.isAuthenticated ? guestLinks : authLinks}
                </div>
                <Menu toggleMenu={toggleMenu} />
                <LocaleButton />
            </div>
        </div>
    )
}

Navbar.propTypes = {
    auth: PropTypes.object.isRequired,
    video: PropTypes.object.isRequired,
    vp: PropTypes.object.isRequired,
}

const mapStateToProps = (state) => ({
    auth: state.auth,
    video: state.ytv,
    vp: state.player,
    currCategory: state.bm.activeCategory,
})

export default connect(mapStateToProps, {
    logout,
    clearPlayer,
    closeVideo,
    clearVideo,
    clearList,
})(Navbar)
