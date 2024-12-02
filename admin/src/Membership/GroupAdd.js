import React from "react";

import { browserHistory } from "../browser_history";
import GroupForm from "../Components/GroupForm";
import Group from "../Models/Group";

const GroupAdd = () => {
    const group = new Group();

    return (
        <div>
            <h2>Skapa grupp</h2>
            <GroupForm
                group={group}
                onSave={() =>
                    group
                        .save()
                        .then(() =>
                            browserHistory.replace(
                                "/membership/groups/" + group.id,
                            ),
                        )
                }
            />
        </div>
    );
};

export default GroupAdd;
