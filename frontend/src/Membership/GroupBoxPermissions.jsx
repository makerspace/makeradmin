import React from 'react';
import Permission from "../Models/Permission";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import {get} from "../gateway";
import * as _ from "underscore";
import Select from "react-select";


const Row = collection => props => {
    const {item} = props;
    return (
        <tr>
            <td>{item.permission}</td>
            <td><a onClick={() => collection.remove(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};


class GroupBoxPermissions extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Permission, url: `/membership/group/${props.params.group_id}/permissions`, idListName: 'permissions', pageSize: 0});
        this.state = {
            showOptions: [],
            selectedOption: null,
        };
        this.options = [];

        get({url: '/membership/permission'}).then(data => {
            this.options = data.data;
            this.setState({showOptions: this.filterOptions()});
        });
    }
    
    componentDidMount() {
        this.unsubscribe = this.collection.subscribe(() => this.setState({showOptions: this.filterOptions()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    filterOptions() {
        const existing = new Set((this.collection.items || []).map(i => i.id));
        return this.options.filter(permission => !existing.has(permission.permission_id));
    }
    
    selectOption(permission) {
        this.setState({selectedOption: permission});
        
        if (_.isEmpty(permission)) {
            return;
        }
        
        this.collection.add(new Permission(permission)).then(this.setState({selectedOption: null}));
    }
    
    render() {
        const columns = [
            {title: "Behörigheter"},
        ];
        
        const {showOptions, selectedOption} = this.state;
        
        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="group">
                        Lägg till behörighet
                    </label>
                    <div className="uk-form-controls">
                        <Select name="group"
                                className="uk-select"
                                tabIndex={1}
                                options={showOptions}
                                value={selectedOption}
                                getOptionValue={p => p.permission_id}
                                getOptionLabel={p => p.permission}
                                onChange={permission => this.selectOption(permission)}
                                isDisabled={!showOptions.length}
                        />
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable emptyMessage="Gruppen har inga behörigheter" rowComponent={Row(this.collection)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}

export default GroupBoxPermissions;