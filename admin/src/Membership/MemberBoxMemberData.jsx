import React from 'react';
import PropTypes from 'prop-types';
import Member from "../Models/Member";
import MemberForm from "../Components/MemberForm";
import {confirmModal} from "../message";
import {withRouter} from "react-router";


class MemberBoxMemberData extends React.Component {
    render() {
        const {router} = this.props;
        
        return (
            <div className='uk-margin-top'>
                <MemberForm
                    member={this.context.member}
                    onSave={() => this.context.member.save()}
                    onDelete={() => {
                        const {member} = this.context;
                        return confirmModal(member.deleteConfirmMessage())
                            .then(() => member.del())
                            .then(() => {
                                router.push("/membership/members/");
                            })
                            .catch(() => null);
                    }}
                />
            </div>
        );
    }
}

MemberBoxMemberData.contextTypes = {
    member: PropTypes.instanceOf(Member)
};


export default withRouter(MemberBoxMemberData);
