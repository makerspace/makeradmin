import React from 'react';
import { Link } from 'react-router';
import Date from '../Components/DateShow';
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import CollectionTable from "../Components/CollectionTable";


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
    const {item, deleteItem} = props;
    return (
        <tr>
            <td><Link to={"/membership/members/" + item.id}>{item.member_number}</Link></td>
            <td>{item.firstname}</td>
            <td>{item.lastname}</td>
            <td>{item.email}</td>
            <td><Date date={item.created_at}/></td>
            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};


class MemberList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Member});
    }

    render() {
        const columns = [
            {title: "#", sort: "member_id"},
            {title: "Förnamn", sort: "firstname"},
            {title: "Efternamn", sort: "lastname"},
            {title: "E-post", sort: "email"},
            {title: "Blev medlem", sort: "created_at"},
            {title: ""},
        ];
        
        return (
            <div>
                <h2>Medlemmar</h2>

                <p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
                <Link to="/membership/members/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny medlem</Link>

                <SearchBox onChange={filters => this.collection.updateFilter(filters)} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}

export default MemberList;
