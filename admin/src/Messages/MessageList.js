import React from "react";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import Message from "../Models/Message";
import DateTimeShow from "../Components/DateTimeShow";
import { Link } from "react-router-dom";
import CollectionNavigation from "../Models/CollectionNavigation";
import SearchBox from "../Components/SearchBox";

const Row = (props) => {
    const { item } = props;
    return (
        <tr>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{Message.statusText(item)}</td>
            <td>{item.recipient}</td>
            <td>
                <Link to={"/messages/" + item.id}>{item.subject}</Link>
            </td>
        </tr>
    );
};

class MessageList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;

        this.collection = new Collection({ type: Message, search, page });
    }

    render() {
        return (
            <div className="uk-margin-top">
                <h2>Utskickshistorik</h2>
                <p>Lista över samtliga utskick.</p>
                <SearchBox
                    handleChange={this.onSearch}
                    value={this.state.search}
                />
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        { title: "Skapad", sort: "created_at" },
                        { title: "Status", sort: "status" },
                        { title: "Mottagare" },
                        { title: "Meddelande", sort: "title" },
                    ]}
                    rowComponent={Row}
                    onPageNav={this.onPageNav}
                />
            </div>
        );
    }
}

export default MessageList;
