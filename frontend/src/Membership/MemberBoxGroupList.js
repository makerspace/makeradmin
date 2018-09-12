import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import Group from "../Models/Group";
import CollectionTable from "../Components/ComponentTable";


const Row = props => {
	const {item, removeItem} = props;
	
	// TODO Remove button should remove buttom from member.
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
        this.collection = new Collection({type: Group});
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
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
				<Link to={"/membership/membersx/" + member_id + "/groups/add"} className="uk-button uk-button-primary"><i className="uk-icon-plus-circle"/> Lägg till gruppp</Link>
			</div>
		);
	}
}

export default MemberBoxGroupList;
