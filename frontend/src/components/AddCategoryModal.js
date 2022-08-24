import '../css/Categories.css'
import { useState, useRef, useEffect } from 'react'
import { CgCloseO } from 'react-icons/cg'
import { connect } from 'react-redux'
import { updateCategories } from '../actions/authActions'
import { returnErrors, clearErrors } from '../actions/errorActions'
import { activeCategory } from '../actions/bmActions'
import PropTypes from 'prop-types'
import ErrorAlert from './ErrorAlert'
import { useTranslation } from 'react-i18next'

const AddCategoryModal = ({
    toggleModal,
    updateCategories,
    err,
    auth,
    addCategoryModal,
    activeCategory,
    returnErrors,
    clearErrors,
}) => {
    const [newCat, setNewCat] = useState('')
    const input = useRef()
    const closemodal = useRef()
    const addCategory = useRef()
    const { t } = useTranslation()

    useEffect(() => {
        if (addCategoryModal) {
            closemodal.current.classList.add('modal-transition')
            addCategory.current.classList.add('modal-transition-1')
        } else return
    }, [addCategoryModal])

    const findDuplicateCategory = (newCat) => {
        if (
            auth.user.categories.find(
                (category) =>
                    category.toLowerCase().trim().replaceAll(' ', '') ===
                    newCat.toLowerCase().trim().replaceAll(' ', '')
            )
        )
            return true
        else return false
    }

    // handle submit
    const handleSubmit = (e) => {
        e.preventDefault()
        // if category exists then return error
        if (findDuplicateCategory(newCat))
            returnErrors('category modal', 400, 'CATEGORY_ERROR')
        // if name is empty string then retur error
        else if (newCat === '')
            returnErrors('category modal', 403, 'CATEGORY_NAME_ERROR')
        else {
            const currentCategories = auth.user.categories
            const updatedCategories = [...currentCategories, newCat]
            // update user categories in database
            updateCategories(updatedCategories)
            // set new category active category
            activeCategory(newCat)
            // assign css classes for effect
            closemodal.current.classList.remove('modal-transition')
            addCategory.current.classList.remove('modal-transition-1')
            // wait for effects and then toggle modal
            setTimeout(() => {
                toggleModal()
            }, 500)
            setNewCat('')
        }
    }

    const closeModal = (e) => {
        e.preventDefault()
        // assign css classes for effect
        closemodal.current.classList.remove('modal-transition')
        addCategory.current.classList.remove('modal-transition-1')
        clearErrors()
        setNewCat('')
        setTimeout(() => {
            toggleModal()
        }, 500)
    }

    // set focus to input field
    useEffect(() => input.current.focus(), [])

    // handle overlay click event
    const handleOverlay = (e) => {
        e.target.classList.contains('modal-overlay') && closeModal(e)
    }

    return (
        <>
            <div
                className="modal-overlay"
                ref={closemodal}
                onClick={(e) => handleOverlay(e)}
            >
                <div className="add-category-modal" ref={addCategory}>
                    <div className="modal-header">
                        <h3>{t('add_new_category')}</h3>
                        <span
                            className="close-btn"
                            onClick={(e) => closeModal(e)}
                        >
                            <CgCloseO className="close-icon" />
                        </span>
                    </div>
                    {err.msg === 'category modal' && <ErrorAlert />}
                    <form onSubmit={handleSubmit}>
                        <input
                            type="text"
                            id="category"
                            name="category"
                            autoComplete="off"
                            ref={input}
                            value={newCat}
                            onChange={(e) => setNewCat(e.target.value.trim())}
                        />
                        <button type="submit">{t('save_category')}</button>
                    </form>
                </div>
            </div>
        </>
    )
}

const mapStateToProps = (state) => ({
    auth: state.auth,
    err: state.error,
})

AddCategoryModal.propTypes = {
    auth: PropTypes.object.isRequired,
    err: PropTypes.object.isRequired,
    updateCategories: PropTypes.func.isRequired,
    activeCategory: PropTypes.func.isRequired,
    returnErrors: PropTypes.func.isRequired,
    clearErrors: PropTypes.func.isRequired,
}

export default connect(mapStateToProps, {
    updateCategories,
    activeCategory,
    returnErrors,
    clearErrors,
})(AddCategoryModal)
