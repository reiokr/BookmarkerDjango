import { useEffect } from 'react';
import '../css/Categories.css';
import BmContainer from './BmContainer';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { updateCategories } from '../actions/authActions';
import { activeCategory } from '../actions/bmActions';
import { clearErrors } from '../actions/errorActions';
import { BsFolderPlus, BsFolderMinus } from 'react-icons/bs';
import AddCategoryModal from './AddCategoryModal';
import ControlBar from './ControlBar';
import { useStateContext } from '../context/ContextProvider';

const Categories = ({
    data,
    auth,
    video,
    updateCategories,
    activeCategory,
    clearErrors,
}) => {
    const {
        addCategoryModal,
        setAddCategoryModal,
        isEmptyCategory,
        categories,
    } = useStateContext();
    const toggleModal = () => {
        setAddCategoryModal((prev) => !prev);
    };
    const handleDelCategory = () => {
        const currentCategories = auth.user.categories;
        const updatedCategories = currentCategories.filter(
            (c) => c !== data.activeCategory
        );
        if (data?.bm?.length === 0) updateCategories(updatedCategories,data.activeCategory);
    };
    const handleChangeCategory = (category) => {
        activeCategory(category);
        clearErrors();
    };

    useEffect(() => {
        if (auth?.isAuthenticated && data?.activeCategory) {
            if (!auth.user.categories.includes(data.activeCategory)) {
                activeCategory(auth.user.categories[0]);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [auth?.user?.categories]);

    if (auth.isAuthenticated) {
        return (
            <>
                <div className="header-buttons">
                    <div className="container">
                        <div className="tab-buttons">
                            {!video.video && data && (
                                <div className="btn-container">
                                    {categories.map((category, i) => {
                                        return (
                                            <button
                                                className={`tab-btn ${
                                                    data?.activeCategory ===
                                                    category
                                                        ? 'active-btn'
                                                        : ''
                                                }`}
                                                key={i}
                                                onClick={() =>
                                                    handleChangeCategory(
                                                        category
                                                    )
                                                }
                                            >
                                                {category}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                            <ControlBar />
                            {!video.video && (
                                <div className="cat-buttons">
                                    {isEmptyCategory && data.isEmptyCategory && (
                                        <div
                                            className="del-cat"
                                            onClick={handleDelCategory}
                                        >
                                            {isEmptyCategory &&
                                                data?.bm?.length === 0 && (
                                                    <BsFolderMinus className="del-cat-icon" />
                                                )}
                                        </div>
                                    )}
                                    <div
                                        className="add-cat"
                                        onClick={toggleModal}
                                    >
                                        <BsFolderPlus className="add-cat-icon" />
                                    </div>
                                </div>
                            )}
                        </div>
                        {addCategoryModal && (
                            <AddCategoryModal
                                toggleModal={toggleModal}
                                addCategoryModal={addCategoryModal}
                            />
                        )}
                    </div>
                </div>
                {auth.isAuthenticated && <BmContainer />}
            </>
        );
    } else {
        return null;
    }
};

const mapStateToProps = (state) => ({
    data: state.bm,
    auth: state.auth,
    video: state.ytv,
});

Categories.propTypes = {
    data: PropTypes.object.isRequired,
    auth: PropTypes.object.isRequired,
    video: PropTypes.object.isRequired,
    updateCategories: PropTypes.func.isRequired,
    activeCategory: PropTypes.func.isRequired,
};

export default connect(mapStateToProps, {
    updateCategories,
    activeCategory,
    clearErrors,
})(Categories);
