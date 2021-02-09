import React from 'react';
import { Link } from 'react-router-dom';
import Collection from "../Models/Collection";
import Key from "../Models/Key";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";
import CollectionNavigation from "../Models/CollectionNavigation";

const Row = props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/membership/keys/" + item.id}>{item.tagid}</Link></td>
            <td><Link to={"/membership/members/" + item.member_id + "/keys"}>{item.member_number}</Link></td>
            <td><DateTimeShow date={item.created_at}/></td>
            <td>{item.description}</td>
        </tr>
    );
};


class KeyList extends CollectionNavigation {

    constructor(props) {
        super(props);
        const {search, page} = this.state;

        this.collection = new Collection({type: Key, expand: "member", search: search, page: page});
    }

    render() {
        const columns = [
            {title: "RFID", sort: "tagid"},
            {title: "Medlem", sort: "member_id"},
            {title: "Skapad", sort: "created_at"},
            {title: "Kommentar", sort: "description"},
        ];
        
        return (
            <div>
                <h2>Nycklar</h2>
                <SearchBox handleChange={this.onSearch} value={this.state.search}/>
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}

export default KeyList;
