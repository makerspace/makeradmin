import React, { useContext } from "react";
import GroupForm from "../Components/GroupForm";
import GroupContext from "../Contexts/GroupContext";
import { confirmModal } from "../message";

const GroupBoxEditInfo = (props) => {
    const { router } = props;
    const group = useContext(GroupContext);

    if (!group) {
        return <div>Group not found</div>;
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

export default GroupBoxEditInfo;
