import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import CollectionTable from "../Components/CollectionTable";
import Key from "../Models/Key";
import {confirmModal} from "../message";


const Row = collection => props => {
	const {item} = props;
	
	const deleteKey = () => {
        return confirmModal(item.deleteConfirmMessage()).then(() => item.del()).then(() => collection.fetch(), () => null);
    };
	
	return (
		<tr>
			<td><Link to={"/membership/keys/" + item.id}>{item.tagid}</Link></td>
			<td>{item.description}</td>
			<td><a onClick={deleteKey} className="removebutton"><i className="uk-icon-trash"/></a></td>
		</tr>
	);
};


class MemberBoxKeys extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Key, url: `/membership/member/${props.params.member_id}/keys`, idListName: 'keys'});
    }
    
    render() {
        const columns = [
            {title: "RFID", sort: "tagid"},
			{title: "Kommentar"},
			{title: ""},
		];

        const {member_id} = this.props.params;

        return (
            <div>
                <div className="uk-margin-top">
                    <CollectionTable rowComponent={Row(this.collection, member_id)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}


export default MemberBoxKeys;
