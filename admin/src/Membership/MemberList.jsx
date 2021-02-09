import React from 'react';
import { Link } from 'react-router-dom';
import Date from '../Components/DateShow';
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import CollectionTable from "../Components/CollectionTable";
import SearchBox from "../Components/SearchBox";
import CollectionNavigation from "../Models/CollectionNavigation";

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


class MemberList extends CollectionNavigation {

    constructor(props) {
        super(props);
        const {search, page} = this.state;
        console.log(this.state);

        this.collection = new Collection({type: Member, search: search, page: page});
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

                <SearchBox handleChange={this.onSearch} value={this.state.search}/>
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}

export default MemberList;
