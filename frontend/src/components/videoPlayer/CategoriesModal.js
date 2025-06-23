import { connect } from 'react-redux';
import { useStateContext } from '../../context/ContextProvider';

const CategoriesModal = ({ auth, data }) => {
    const {
        setShowCategories,
        activeId,
        setActiveId,
        saveToBookmarks,
        setShowInfoModal,
        setAddCategoryModal,
        categories,
        bookmarkType,
        setSaveToCategory,
        setChangeActiveCategory,
    } = useStateContext();
    const reversedList = [...categories].reverse();
    const toggleModal = () => {
        setChangeActiveCategory(false);
        setAddCategoryModal((prev) => !prev);
    };

    const handleSaveToBookmarks = (c) => {
        setShowInfoModal(false);
        setSaveToCategory((prev) => c);
        saveToBookmarks(activeId, c, bookmarkType);
    };

    return (
        <div className="categories-modal">
            <p className="categories-modal-title">Choose category</p>
            <div className="categories-modal-body">
                {reversedList &&
                    reversedList.map((c) => {
                        return (
                            <li
                                style={{ cursor: 'pointer' }}
                                key={c}
                                onClick={() => {
                                    handleSaveToBookmarks(c);
                                }}
                            >
                                <p>{c}</p>
                            </li>
                        );
                    })}
            </div>
            <div className="categories-modal-buttons">
                <button onClick={toggleModal}>New category</button>
                <button
                    onClick={() => {
                        setShowCategories(false);
                        setActiveId(null);
                    }}
                >
                    Cancel
                </button>
            </div>
        </div>
    );
};

const mapStateToProps = (state) => ({
    auth: state.auth,
    data: state.bm,
});

export default connect(mapStateToProps)(CategoriesModal);
