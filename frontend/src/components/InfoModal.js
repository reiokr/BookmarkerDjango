import {useStateContext} from '../context/ContextProvider'

const InfoModal = ({content}) => {
  const {saveToCategory} = useStateContext()
  return (
      <div className="info-modal">
          <h3>
              {content}
              {saveToCategory && <span className="info-modal-category">{saveToCategory}</span>}
          </h3>
      </div>
  );
}

export default InfoModal