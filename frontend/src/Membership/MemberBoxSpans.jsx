import React from 'react';
import PropTypes from 'prop-types';
import Member from "../Models/Member";
import {withRouter} from "react-router";


class MemberBoxSpans extends React.Component {
    render() {
        const {router} = this.props;
        
        return (
            <div className='uk-margin-top'>
                Översikt.
            </div>
        );
    }
}

MemberBoxSpans.contextTypes = {
    member: PropTypes.instanceOf(Member)
};


export default withRouter(MemberBoxSpans);