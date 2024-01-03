import React from "react";
import { Link } from "react-router-dom";
import GiftCard from "../Models/GiftCard";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";
import CollectionNavigation from "../Models/CollectionNavigation";

const Row = (props) => {
    const { item } = props;
    return (
        <tr>
            <td>
                <Link to={"/sales/gift-card/" + item.id}>{item.id}</Link>
            </td>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{item.status}</td>
            <td>{item.email}</td>
        </tr>
    );
};

class GiftCardList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;

        this.collection = new Collection({
            type: GiftCard,
            url: "/webshop/gift-card",
            search,
            page,
        });
    }

    render() {
        const columns = [
            { title: "Presentkort" },
            { title: "Skapad" },
            { title: "Status" },
            { title: "Email" },
        ];

        return (
            <div className="uk-margin-top">
                <h2>Presentkort</h2>
                <SearchBox
                    handleChange={this.onSearch}
                    value={this.state.search}
                />
                <CollectionTable
                    emptyMessage="Inga presentkort"
                    rowComponent={Row}
                    collection={this.collection}
                    columns={columns}
                    onPageNav={this.onPageNav}
                />
            </div>
        );
    }
}

export default GiftCardList;
