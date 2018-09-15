import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import Group from "../Models/Group";
import CollectionTable from "../Components/CollectionTable";
import {get} from "../gateway";
import Select from "react-select";
import * as _ from "underscore";


const Row = collection => props => {
    const {item} = props;
    
    return (
        <tr>
            <td><Link to={"/membership/groups/" + item.id}>{item.title}</Link></td>
            <td>{item.num_members}</td>
            <td><a onClick={() => collection.remove(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};


class MemberBoxGroups extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Group, url: `/membership/member/${props.params.member_id}/groups`, idListName: 'groups'});
        this.state = {options: [], selectedOption: null};
        
        get({url: '/membership/group'}).then(data => this.setState({options: data.data}));
    }

    selectOption(member_id, group) {
        this.setState({selectedOption: group});
        
        if (_.isEmpty(group)) {
            return;
        }
        
        this.collection.add(new Group(group)).then(this.setState({selectedOption: null}));
    }
    
    render() {
        const columns = [
            {title: "Titel", sort: "title"},
            {title: "Antal medlemmar"},
            {title: ""},
        ];
  
        const {member_id} = this.props.params;
        const {selectedOption, options} = this.state;
        
        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="group">
                        Lägg till grupp:
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
                    <CollectionTable rowComponent={Row(this.collection, member_id)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}

export default MemberBoxGroups;
