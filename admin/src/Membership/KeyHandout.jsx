import React from 'react';
import PropTypes from 'prop-types';
import Member from "../Models/Member";
import Key from "../Models/Key"
import KeyHandoutForm from "../Components/KeyHandoutForm";
import {confirmModal} from "../message";
import {withRouter} from "react-router";


class KeyHandout extends React.Component {
    render() {
        const {router} = this.props;
        
        return (
            <div className='uk-margin-top'>
                <KeyHandoutForm
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

KeyHandout.contextTypes = {
    member: PropTypes.instanceOf(Member)
};

export default withRouter(KeyHandout);
