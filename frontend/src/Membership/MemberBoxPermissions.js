import React from 'react';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Permission from "../Models/Permission";


const Row = props => <tr><td>{props.item.permission}</td></tr>;


class MemberBoxPermissions extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Permission, url: `/membership/member/${props.params.member_id}/permissions`, pageSize: 0});
    }
    
    render() {
        const columns = [
            {title: "Behörighet"},
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable emptyMessage="Medlemmen har inga behörigheter" rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}

export default MemberBoxPermissions;
