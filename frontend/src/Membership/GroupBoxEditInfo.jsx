import React from 'react';
import PropTypes from 'prop-types';
import Group from "../Models/Group";
import GroupForm from "../Components/GroupForm";
import {confirmModal} from "../message";
import {withRouter} from "react-router";

class GroupBoxEditInfo extends React.Component {
    
    render() {
        const {router} = this.props;
        
        return (
            <div className='uk-margin-top'>
                <GroupForm
                    group={this.context.group}
                    onSave={() => this.context.group.save()}
                    onDelete={() => {
                        const {group} = this.context;
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
    group: PropTypes.instanceOf(Group)
};


export default withRouter(GroupBoxEditInfo);