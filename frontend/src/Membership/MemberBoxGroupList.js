import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import Group from "../Models/Group";
import CollectionTable from "../Components/CollectionTable";
import {del} from "../gateway";


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
			<td><Link to={"/membership/membersx/" + item.id}>{item.title}</Link></td>
			<td>{item.num_members}</td>
			<td><a onClick={() => removeItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
		</tr>
	);
};


class MemberBoxGroupList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Group, filter: {member_id: props.params.member_id}});
    }

    render() {
        const columns = [
            {title: "Titel", sort: "title"},
			{title: "Antal medlemmar"},
			{title: ""},
		];
  
        const {member_id} = this.props.params;
        
		return (
			<div>
                <CollectionTable rowComponent={Row(this.collection, member_id)} collection={this.collection} columns={columns} />
				<Link to={"/membership/membersx/" + member_id + "/groups/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle"/> Lägg till gruppp</Link>
			</div>
		);
	}
}

export default MemberBoxGroupList;
