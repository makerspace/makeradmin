import React from 'react';
import PropTypes from 'prop-types';
import Member from "../../Models/Member";
import MemberForm from "../Components/MemberForm";

export default class MemberInfoTab extends React.Component {
	render() {
        return (
            <div>
                <MemberForm member={this.context.member} />
            </div>
        );
    }
}

MemberInfoTab.contextTypes = {
    member: PropTypes.instanceOf(Member)
};
