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


class MemberBoxGroups extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Group, filter: {member_id: props.params.member_id}});
        this.state = {options: [], selectedOption: null};
        
        get({url: '/membership/group'}).then(data => this.setState({options: data.data}));
    }

    loadOptions(inputValue, callback) {
        const params = inputValue ? {search: inputValue} : null;
        get({url: '/membership/group', params}).then(data => callback(data.data));
    }
    
    selectOption(member_id, group) {
        this.setState({selectedOption: group});
        
        if (_.isEmpty(group)) {
            return;
        }
        
        post({url: "/membership/member/" + member_id + "/groups/add", data: {groups: [group.group_id]}, expectedDataStatus: null})
            .then(() => {
                this.setState({selectedOption: null});
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
