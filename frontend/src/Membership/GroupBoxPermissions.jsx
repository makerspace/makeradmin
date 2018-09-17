import React from 'react';
import PropTypes from 'prop-types';
import Group from "../Models/Group";
import GroupForm from "./Components/GroupForm";
import {confirmModal} from "../message";
import {withRouter} from "react-router";
import {Select} from "react-select";
import CollectionTable from "../Components/CollectionTable";

class GroupBoxPermissions extends React.Component {
    
    
    
    render() {
        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="group">
                        Lägg till i grupp
                    </label>
                    <div className="uk-form-controls">
                        <Select name="group"
                                className="uk-select"
                                tabIndex={1}
                                options={options}
                                value={selectedOption}
                                getOptionValue={g => g.group_id}
                                getOptionLabel={g => g.title}
                                onChange={group => this.selectOption(member_id, group)}
                        />
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable emptyMessage="Inte med i några grupper" rowComponent={Row(this.collection, member_id)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}

export default GroupBoxPermissions;