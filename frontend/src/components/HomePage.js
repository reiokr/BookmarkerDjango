import React from 'react'
import '../css/Home.css';
import {useTranslation} from 'react-i18next'

const HomePage = () => {
  const {t} = useTranslation()
  return (
    <>
      <br />
      <div className='homepage container'>
        <h2>{t("Welcome to the Bookmarker HomePage")}</h2>
      </div>
    </>
  );
}

export default HomePage
