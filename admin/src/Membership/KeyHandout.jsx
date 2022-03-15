import React from 'react';
import PropTypes from 'prop-types';
import Member from "../Models/Member";
import KeyHandoutForm from "../Components/KeyHandoutForm";
import {withRouter} from "react-router";


class KeyHandout extends React.Component {
    render() {
        const {router} = this.props;
        
        return (
            <div className='uk-margin-top'>
                <KeyHandoutForm
                    member={this.context.member}
                />
            </div>
        );
    }
}

KeyHandout.contextTypes = {
    member: PropTypes.instanceOf(Member)
};

export default withRouter(KeyHandout);
