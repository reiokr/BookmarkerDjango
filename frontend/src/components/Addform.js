import '../css/Addform.css';
import React, { useState, useEffect, useRef } from 'react';
import { connect } from 'react-redux';
import { addBookmark} from '../actions/bmActions';
import {clearErrors} from '../actions/errorActions';
import PropTypes from 'prop-types';
import Collapse from '@mui/material/Collapse';
import Alert from '@mui/material/Alert';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import ErrorAlert from './ErrorAlert';
import { useTranslation } from 'react-i18next'


const Addform = ({
  addBookmark,
  clearErrors,
  isAuthenticated,
  data,
  video,
  err
}) => {
  const [open, setOpen] = React.useState(false);
  const [url, setUrl] = useState('');
  const addRef = useRef();
  const { t } = useTranslation()

  const handleChange = (newUrl) => {
    setUrl(newUrl);
  };

  // submit data and send to server
  const handleSubmit = (e) => {
    e.preventDefault();
    if (url) {
      const newBm = { url, category: localStorage.getItem('activeCat') };
      addBookmark(newBm);
      clearErrors();
      setUrl('');
    }
  };

  useEffect(() => {
    if(data?.urlError.error){
      setOpen(true)
    }
    else setOpen(false);
  }, [data.urlError]);

  return (
    <>
      {isAuthenticated && !video.video && (
        <div className='container'>
          <div className='add-form'>
          {err.id==="ADD_BM_ERROR"&&<ErrorAlert/>}
            {open && (
              <Collapse in={open}>
                <Alert
                  variant='filled'
                  severity='error'
                  action={
                    <IconButton
                      aria-label='close'
                      color='default'
                      size='small'
                      onClick={() => {
                        setOpen(false)
                      }}
                    >
                      <CloseIcon fontSize='inherit' />
                    </IconButton>
                  }
                  sx={{ mb: 2 }}
                >
                  <p style={{ color: 'white' }}>{data?.urlError?.error}</p>
                </Alert>
              </Collapse>
            )}
            <form onSubmit={handleSubmit}>
              <input
                ref={addRef}
                type='text'
                name='add'
                id='add'
                autoComplete='off'
                placeholder='www.website.com'
                value={url}
                onChange={(e) => handleChange(e.target.value)}
              />
              <button type='submit'>{t('add_btn')}</button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
const mapStateToProps = (state) => ({
  data: state.bm,
  video: state.ytv,
  isAuthenticated: state.auth.isAuthenticated,
  err: state.error
});

Addform.propTypes = {
  video: PropTypes.object.isRequired,
  data: PropTypes.object.isRequired,
  addBookmark: PropTypes.func.isRequired,
};
export default connect(mapStateToProps, { addBookmark, clearErrors})(
  Addform
);
