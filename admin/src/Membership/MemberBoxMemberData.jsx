import PropTypes from "prop-types";
import React from "react";
import { withRouter } from "react-router";
import MemberForm from "../Components/MemberForm";
import Member from "../Models/Member";
import auth from "../auth";
import { confirmModal } from "../message";

class MemberBoxMemberData extends React.Component {
    update_member_info(member_id) {
        auth.update_member_info(member_id);
    }

    render() {
        const { router } = this.props;

        return (
            <div className="uk-margin-top">
                <MemberForm
                    member={this.context.member}
                    onSave={() => {
                        this.update_member_info(this.context.member.member_id);
                        this.context.member.save();
                    }}
                    onDelete={() => {
                        const { member } = this.context;
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
    member: PropTypes.instanceOf(Member),
};

export default withRouter(MemberBoxMemberData);
