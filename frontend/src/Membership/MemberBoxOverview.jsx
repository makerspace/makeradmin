import React from 'react';
import PropTypes from 'prop-types';
import Member from "../Models/Member";


class MemberBoxOverview extends React.Component {
    render() {
        const {member} = this.context;
        
        return (
            <div className='uk-margin-top'>
                {member.member_number} {member.firstname} {member.lastname}
            </div>
        );
    }
}

MemberBoxOverview.contextTypes = {
    member: PropTypes.instanceOf(Member)
};


export default MemberBoxOverview;