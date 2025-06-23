import {useTranslation} from 'react-i18next'
const NotFound = () => {
  const {t} = useTranslation()
  return <div>{t('Page not found')}</div>
};

export default NotFound;
