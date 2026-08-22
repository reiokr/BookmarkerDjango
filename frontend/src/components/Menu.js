import '../scss/Navbar.scss'
import { GiHamburgerMenu } from 'react-icons/gi'

const Menu = ({ toggleMenu }) => {
  return (
    <div className="menu-btn">
      <GiHamburgerMenu className='menu-icon' onClick={toggleMenu} />
    </div>
  )
}

export default Menu
