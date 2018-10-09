import React from 'react';
import { Link } from 'react-router';
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Group from "../Models/Group";


class SearchBox extends React.Component {
    
    constructor(props) {
        super(props);
    }
    
    render() {
        return (
            <div className="filterbox">
                <div className="uk-grid">
                    <form className="uk-form">
                        <div className="uk-form-icon">
                            <i className="uk-icon-search"/>
                            <input ref="search" tabIndex="1" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord"
                                   onChange={() => this.props.onChange({search: this.refs.search.value})} />
                        </div>
                    </form>
                </div>
            </div>
        );
    }
}


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
        this.collection = new Collection({type: Group});
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

                <SearchBox onChange={filters => this.collection.updateFilter(filters)} />
                <CollectionTable rowComponent={Row} collection={this.collection} columns={columns} />
            </div>
        );
    }
}

export default GroupList;
