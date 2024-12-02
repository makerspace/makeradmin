import PropTypes from "prop-types";
import React from "react";
import { withRouter } from "react-router";
import GroupForm from "../Components/GroupForm";
import { confirmModal } from "../message";
import Group from "../Models/Group";

const GroupBoxEditInfo = (props, context) => {
    const { router } = props;

    return (
        <div className="uk-margin-top">
            <GroupForm
                group={context.group}
                onSave={() => context.group.save()}
                onDelete={() => {
                    const { group } = context;
                    confirmModal(group.deleteConfirmMessage())
                        .then(() => group.del())
                        .then(() => {
                            router.push("/membership/groups/");
                        })
                        .catch(() => null);
                }}
            />
        </div>
    );
};

GroupBoxEditInfo.contextTypes = {
    group: PropTypes.instanceOf(Group),
};

export default withRouter(GroupBoxEditInfo);
