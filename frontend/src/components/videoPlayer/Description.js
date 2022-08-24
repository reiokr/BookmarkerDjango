import '../../css/Description.css'
import { connect } from 'react-redux'
import PropTypes from 'prop-types'
import FormatText from './FormatText'
import {useStateContext} from '../../context/ContextProvider'


const Description = ({ description }) => {
  const {
      showdesc,
      timestampControl,
      setTimestampControl,
      timestampPreviousTime,
  } = useStateContext()
    return (
        <div className="modal-body">

            {!showdesc && (
                <FormatText
                    description={description}
                    timestampControl={timestampControl}
                    setTimestampControl={setTimestampControl}
                    timestampPreviousTime={timestampPreviousTime}
                />
            )}
        </div>
    );
}

const mapStateToProps = (state) => ({
    video: state.ytv,
})

Description.propTypes = {
    video: PropTypes.object.isRequired,
}

export default connect(mapStateToProps)(Description)
