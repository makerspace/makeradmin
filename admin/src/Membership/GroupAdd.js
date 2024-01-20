import { browserHistory } from "../browser_history";
import GroupForm from "../Components/GroupForm";
import Group from "../Models/Group";
import React from "react";
class GroupAdd extends React.Component {
    constructor(props) {
        super(props);
        this.group = new Group();
    }

    render() {
        return (
            <div>
                <h2>Skapa grupp</h2>
                <GroupForm
                    group={this.group}
                    onSave={() =>
                        this.group
                            .save()
                            .then(() =>
                                browserHistory.replace(
                                    "/membership/groups/" + this.group.id,
                                ),
                            )
                    }
                />
            </div>
        );
    }
}

export default GroupAdd;
