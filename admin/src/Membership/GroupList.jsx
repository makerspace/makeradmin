import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Date from "../Components/DateShow";
import Icon from "../Components/icons";
import SearchBox from "../Components/SearchBox";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import { withCollectionNavigationProps } from "../Models/CollectionNavigation";
import Group from "../Models/Group";

const Row = (props) => {
    const { item, deleteItem } = props;

    return (
        <tr>
            <td>
                <Link to={"/membership/groups/" + item.id}>{item.title}</Link>
            </td>
            <td>
                <Link to={"/membership/groups/" + item.id}>{item.name}</Link>
            </td>
            <td>{item.num_members}</td>
            <td>
                <Date date={item.created_at} />
            </td>
            <td>
                <a onClick={() => deleteItem(item)} className="removebutton">
                    <Icon icon="trash" />
                </a>
            </td>
        </tr>
    );
};

class GroupList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;

        this.collection = new Collection({
            type: Group,
            search: search,
            page: page,
        });
    }

    render() {
        const columns = [
            { title: "Titel", sort: "title" },
            { title: "Namn", sort: "name" },
            { title: "Antal medlemmar" },
            { title: "Skapad", sort: "created_at" },
            { title: "" },
        ];

        return (
            <div>
                <h2>Grupper</h2>

                <p className="uk-float-left">
                    På denna sida ser du en lista på samtliga grupper..
                </p>
                <Link
                    to="/membership/groups/add"
                    className="uk-button uk-button-primary uk-float-right"
                >
                    <Icon icon="plus-circle" /> Skapa ny grupp
                </Link>

                <SearchBox
                    handleChange={this.onSearch}
                    value={this.state.search}
                />
                <CollectionTable
                    rowComponent={Row}
                    collection={this.collection}
                    columns={columns}
                    onPageNav={this.onPageNav}
                />
            </div>
        );
    }
}

export default withCollectionNavigationProps(GroupList);
