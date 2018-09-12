import React from 'react';
import PropTypes from 'prop-types';
import Member from "../../Models/Member";
import MemberForm from "../Components/MemberForm";
import {confirmModal} from "../../message";
import {withRouter} from "react-router";

class MemberInfoTab extends React.Component {
	render() {
        const {router} = this.props;
        
        return (
            <div>
                <MemberForm
                    member={this.context.member}
                    onSave={() => this.context.member.save()}
                    onRemove={() => {
                        const {member} = this.context;
                        return confirmModal(member.removeConfirmMessage())
                            .then(() => member.remove(), () => false)
                            .then(() => {
                                router.push("/membership/membersx/");
                            });
                    }}
                />
            </div>
        );
    }
}

MemberInfoTab.contextTypes = {
    member: PropTypes.instanceOf(Member)
};


export default withRouter(MemberInfoTab);