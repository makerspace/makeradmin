import React from "react";

import GroupForm from "../Components/GroupForm";
import Group from "../Models/Group";
import { useNavigate } from "react-router";

const GroupAdd = () => {
    const group = new Group();
    const navigate = useNavigate();

    return (
        <div>
            <h2>Skapa grupp</h2>
            <GroupForm
                group={group}
                onSave={() =>
                    group.save().then(() =>
                        navigate("/membership/groups/" + group.id, {
                            replace: true,
                        }),
                    )
                }
            />
        </div>
    );
};

export default GroupAdd;
