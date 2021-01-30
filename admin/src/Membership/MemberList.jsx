import React from 'react';
import { Link } from 'react-router-dom';
import Date from '../Components/DateShow';
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import CollectionTable from "../Components/CollectionTable";
import SearchBox from "../Components/SearchBox";

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
        this.onSearch = this.onSearch.bind(this);
        this.onPageNav = this.onPageNav.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        const page = this.params.get('page') || 1;
        this.collection = new Collection({type: Member, search: search_term, page: page});
        this.state = {'search': search_term, 'page_index': page};
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

    onPageNav(index) {
        this.setState({'page_index': index});
        this.collection.updatePage(index);
        this.params.set("page", index);
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
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

                <SearchBox handleChange={this.onSearch} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}

export default MemberList;
