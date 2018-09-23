import React from 'react';
import { Link } from 'react-router';
import Date from '../Components/DateShow';
import Collection from "../Models/Collection";
import Key from "../Models/Key";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";


class SearchBox extends React.Component {
    
    constructor(props) {
        super(props);
    }
    
    render() {
        return (
            <div className="filterbox">
                <div className="uk-grid">
                    <div className="uk-width-2-3">
                        <form className="uk-form">
                            <div className="uk-form-icon">
                                <i className="uk-icon-search"/>
                                <input ref="search" tabIndex="1" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord"
                                       onChange={() => this.props.onChange({search: this.refs.search.value})} />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


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
        this.collection = new Collection({type: Key, expand: "member"});
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
                <SearchBox onChange={filters => this.collection.updateFilter(filters)} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}

export default KeyList;
