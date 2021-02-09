import React from 'react';
import { Link } from 'react-router-dom';
import Collection from "../Models/Collection";
import Key from "../Models/Key";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";

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


class KeyList extends React.Component {

    constructor(props) {
        super(props);
        this.onSearch = this.onSearch.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        this.collection = new Collection({type: Key, expand: "member", search: search_term});
        this.state = {'search': search_term};
    }

    onSearch(term) {
        this.setState({'search': term});
        this.collection.updateSearch(term);
        if (term === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", term);
        }
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
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
                <SearchBox handleChange={this.onSearch} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}

export default KeyList;
