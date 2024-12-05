import React, { useContext } from "react";
import { withRouter } from "react-router";
import GroupForm from "../Components/GroupForm";
import GroupContext from "../Contexts/GroupContext";
import { confirmModal } from "../message";

const GroupBoxEditInfo = (props) => {
    const { router } = props;
    const group = useContext(GroupContext); // Access the group from context

    if (!group) {
        return <div>Group not found</div>; // Handle missing context gracefully
    }

    return (
        <div className="uk-margin-top">
            <GroupForm
                group={group}
                onSave={() => group.save()}
                onDelete={() => {
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

export default withRouter(GroupBoxEditInfo);
