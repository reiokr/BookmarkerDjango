import { useState, useEffect, useRef } from 'react';
import '../css/ControlBar.css';
import { BiSort, BiSearchAlt } from 'react-icons/bi';
import { connect } from 'react-redux';
import { sortItems, filterBookmarks } from '../actions/bmActions';
import {clearErrors } from '../actions/errorActions'
import PropTypes from 'prop-types';
import { useStateContext } from '../context/ContextProvider';

const ControlBar = ({
  sortItems,
  filterBookmarks,
  clearErrors,
  video,
  bm
}) => {
  const { newsize, handleSizeChange } = useStateContext()
  const [sort, setSort] = useState(true);
  const [search, setSearch] = useState('');
  const refSearch = useRef();

  const toggleSort = () => {
    setSort(!sort);
    clearErrors();
  };

  useEffect(() => {
    sortItems(sort, bm.activeCategory);
    clearErrors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort]);
  
  
  useEffect(() => {
    filterBookmarks(search, bm.activeCategory);
    clearErrors();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ search, filterBookmarks, bm.activeCategory]);

  useEffect(() => {
    setSearch('')
  },[bm.activeCategory])


  return (
    <>
      {!video?.video && (
        <div className='control-bar-container'>
          <div className='controlBar-icon' onClick={toggleSort}>
            <BiSort className='sort-icon' />
          </div>
          <form >
            <input
              type='text'
              id='sort'
              name='sort'
              autoComplete='off'
              ref={refSearch}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button type='submit'>
              <BiSearchAlt className='search-icon' />
            </button>
          </form>
        </div>
      )}
      {video?.video && (
        <div className='slidecontainer'>
          <input
            className='slider'
            type='range'
            id='player-width'
            name='player-width'
            min='1.4'
            max='8'
            value={newsize}
            step='0.05'
            onChange={(e) => handleSizeChange(e.target.value)}
          />
        </div>
      )}
    </>
  );
};

const mapStateToProps = (state) => ({
  vp: state.player,
  video: state.ytv,
  bm: state.bm,
});

ControlBar.propTypes = {
  vp: PropTypes.object.isRequired,
  video: PropTypes.object.isRequired,
  sortItems: PropTypes.func.isRequired,
  filterBookmarks: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, { sortItems, filterBookmarks, clearErrors })(ControlBar);
