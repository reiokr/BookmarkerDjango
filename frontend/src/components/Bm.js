import { useState, useEffect } from 'react';
import '../css/Bm.css';
import { CgCloseO } from 'react-icons/cg';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { deleteItem } from '../actions/bmActions';
import DescModal from './videoPlayer/DescModal';
import Fade from '@mui/material/Fade';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import {useTranslation} from 'react-i18next'

const Bm = ({ item, deleteItem, data }) => {
  const [showmodal, setShowmodal] = useState(false);
  const [titleLoaded, setTitleLoaded] = useState(false);
  const { title, image_url, id, url, description, type } = item;
  const {t} = useTranslation()

  const handleTitle = () => {
    setShowmodal(!showmodal);
  };

  useEffect(() => {
    if (title) {
      setTitleLoaded(true);
    } else setTitleLoaded(false);
  }, [title]);

  function srcset(image, width, height, rows = 1, cols = 1) {
    return {
      src: `${image}?w=${width * cols}&h=${height * rows}&fit=crop&auto=format`,
      srcSet: `${image}?w=${width * cols}&h=${
        height * rows
      }&fit=crop&auto=format&dpr=2 2x`,
    };
  }

  return (
    <>
      {showmodal && (
        <DescModal
          description={description}
          thumbnails={[]}
          type={type}
          handleTitle={handleTitle}
        />
      )}
      <Fade in={titleLoaded} timeout={500}>
        <div className='bm-main'>
          <a href={url} className='bookmark' target='_blank' rel='noreferrer'>
            <span className='go-to-web'>{t('go_to_website')}</span>
          </a>
          <ImageList
            sx={{
              width: 'auto',
              maxWidth: 380,
              maxHeight: 210,
              // Promote the list into its own layer in Chrome. This costs memory, but helps keeping high FPS.
              transform: 'translateZ(0)',
            }}
            rowHeight={200}
            gap={1}
          >
            {image_url.map((item) => {
              const cols = item ? 2 : 1;
              const rows = item ? 1 : 1;
              return (
                <ImageListItem key={item} cols={cols} rows={rows}>
                  <img
                    className='bm-img'
                    {...srcset(item, 189, 200, rows, cols)}
                    alt={item}
                  />
                </ImageListItem>
              );
            })}
          </ImageList>
          <div className='title' onClick={handleTitle}>
            {title}
          </div>
          <div className='close-btn-bm'>
            <CgCloseO
              className='close-icon'
              onClick={() => deleteItem(id, data.activeCategory)}
            />
          </div>
        </div>
      </Fade>
    </>
  );
};

const mapStateToProps = (state) => ({
  data: state.bm,
});

Bm.propTypes = {
  data: PropTypes.object.isRequired,
  deleteItem: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, { deleteItem })(Bm);
