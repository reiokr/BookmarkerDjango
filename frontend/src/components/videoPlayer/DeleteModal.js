import {useTranslation} from 'react-i18next'

const DeleteModal = ({ handleDelete, setDeleteModal }) => {
  const {t} = useTranslation()
    const deleteModal = () => {
        handleDelete()
    }
    const cancelDelete = () => {
        setDeleteModal(false)
    }

    return (
        <div className="description-container">
            <div className="delete-modal">
                <p>{t('Delete this bookmark?')}</p>
                <div className="delete-item">
                    <button onClick={deleteModal}>{t("Yes")}</button>
                    <button onClick={cancelDelete}>{t("No")}</button>
                </div>
            </div>
        </div>
    )
}

export default DeleteModal
