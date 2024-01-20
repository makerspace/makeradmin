import GroupForm from "../Components/GroupForm";
import { confirmModal } from "../message";
import Group from "../Models/Group";
import PropTypes from "prop-types";
import { withRouter } from "react-router";
import React from "react";
class GroupBoxEditInfo extends React.Component {
    render() {
        const { router } = this.props;

        return (
            <div className="uk-margin-top">
                <GroupForm
                    group={this.context.group}
                    onSave={() => this.context.group.save()}
                    onDelete={() => {
                        const { group } = this.context;
                        return confirmModal(group.deleteConfirmMessage())
                            .then(() => group.del())
                            .then(() => {
                                router.push("/membership/groups/");
                            })
                            .catch(() => null);
                    }}
                />
            </div>
        );
    }
}

GroupBoxEditInfo.contextTypes = {
    group: PropTypes.instanceOf(Group),
};

export default withRouter(GroupBoxEditInfo);
