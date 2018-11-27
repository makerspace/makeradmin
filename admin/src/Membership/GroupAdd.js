import React from 'react';

import GroupForm from '../Components/GroupForm';
import {browserHistory} from 'react-router';
import Group from "../Models/Group";


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
                    onSave={() => this.group.save().then(() => browserHistory.replace('/membership/groups/' + this.group.id))}
                />
            </div>
        );
    }
}

export default GroupAdd;
