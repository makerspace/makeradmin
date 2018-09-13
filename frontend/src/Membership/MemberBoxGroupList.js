import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import Group from "../Models/Group";
import CollectionTable from "../Components/CollectionTable";
import {del, get, post} from "../gateway";
import Select from "react-select";
import * as _ from "underscore";


const Row = (collection, member_id) => props => {
	const {item} = props;
	
	const removeItem = i => {
        del({
                url: "/membership/member/" + member_id + "/groups/remove",
                data: {groups: [i.id]},
                options: {method: 'POST'},
                expectedDataStatus: null,
        })
            .then(() => {collection.fetch();}, () => null);
    };
	
	return (
		<tr>
			<td><Link to={"/membership/groups/" + item.id}>{item.title}</Link></td>
			<td>{item.num_members}</td>
			<td><a onClick={() => removeItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
		</tr>
	);
};


class MemberBoxGroupList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Group, filter: {member_id: props.params.member_id}});
        this.state = {selectedGropuIds: [], options: [], selectedOption: null};
        get({url: '/membership/group'}).then(data => this.setState({options: data.data}));
    }

    loadOptions(inputValue, callback) {
        const params = inputValue ? {search: inputValue} : null;
        get({url: '/membership/group', params}).then(data => callback(data.data));
    }
    
    addGroups(member_id, selectedGropuIds) {
        post({
                 url: "/membership/member/" + member_id + "/groups/add",
                 data: {groups: selectedGropuIds},
                 expectedDataStatus: null,
             })
            .then(() => {
                this.setState({selectedGropuIds: []});
                return this.collection.fetch();
            });
    }
    
    render() {
        const columns = [
            {title: "Titel", sort: "title"},
			{title: "Antal medlemmar"},
			{title: ""},
		];
  
        const {member_id} = this.props.params;
        const {selectedGropuIds, options} = this.state;
        
		return (
			<div>
                <div className="uk-grid uk-margin-top">
                    <div className="uk-width-4-5">
                        <Select
                            isMulti
                            options={options}
                            getOptionValue={g => g.group_id}
                            getOptionLabel={g => g.title}
                            onChange={groups => this.setState({selectedGropuIds: groups.map(g => g.group_id)})}
                        />
                    </div>
                    <div className="uk-width-1-5">
                        <button disabled={_.isEmpty(selectedGropuIds)} className="uk-button uk-button-primary" onClick={() => this.addGroups(member_id, selectedGropuIds)}>
                            <i className="uk-icon-plus-circle"/> Lägg till
                        </button>
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable rowComponent={Row(this.collection, member_id)} collection={this.collection} columns={columns} />
                </div>
			</div>
		);
	}
}

export default MemberBoxGroupList;
