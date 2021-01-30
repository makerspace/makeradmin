import React from 'react';
import { Link } from 'react-router-dom';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Group from "../Models/Group";
import SearchBox from "../Components/SearchBox";

const Row = props => {
    const {item, deleteItem} = props;
    
    return (
        <tr>
            <td><Link to={"/membership/groups/" + item.id}>{item.title}</Link></td>
            <td><Link to={"/membership/groups/" + item.id}>{item.name}</Link></td>
            <td>{item.num_members}</td>
            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};


class GroupList extends React.Component {

    constructor(props) {
        super(props);
        this.onSearch = this.onSearch.bind(this);
        this.onPageNav = this.onPageNav.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        const page = this.params.get('page') || 1;
        this.collection = new Collection({type: Group, search: search_term, page: page});
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
            {title: "Titel", sort: "title"},
            {title: "Namn", sort: "name"},
            {title: "Antal medlemmar"},
            {title: ""},
        ];
        
        return (
            <div>
                <h2>Grupper</h2>

                <p className="uk-float-left">På denna sida ser du en lista på samtliga grupper..</p>
                <Link to="/membership/groups/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny grupp</Link>

                <SearchBox handleChange={this.onSearch} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} onPageNav={this.onPageNav} />
            </div>
        );
    }
}

export default GroupList;
