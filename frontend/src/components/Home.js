import '../css/Home.css';
import { connect } from 'react-redux';
import Loader from './Loader';
import Categories from './Categories';
import Addform from './Addform';
import HomePage from './HomePage';
import PropTypes from 'prop-types';

const Home = ({ auth }) => {

  return (
    <>
      <Addform />
      <Categories />
      {auth.isLoading && auth.isAuthenticated && <Loader />}
      {!auth.isAuthenticated && <HomePage />}
    </>
  );
};

const mapStateToProps = (state) => ({
  auth: state.auth,
});

Home.porpTypes = {
  auth: PropTypes.object.isRequired,
};

export default connect(mapStateToProps, {})(Home);
