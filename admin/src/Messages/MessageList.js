import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import SearchBox from "../Components/SearchBox";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import { withCollectionNavigationProps } from "../Models/CollectionNavigation";
import Message from "../Models/Message";

function truncate(input, n) {
    if (input.length > n) {
        return input.substring(0, n - 3) + "...";
    }
    return input;
}

function unescapeHtml(html) {
    // Wow, such a silly solution
    const txt = document.createElement("textarea");
    txt.innerHTML = html;
    return txt.value;
}

const Row = (props) => {
    const { item } = props;

    return (
        <tr>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{Message.statusText(item)}</td>
            <td>
                <Link to={`/membership/members/${item.member_id}`}>
                    {item.recipient}
                </Link>
            </td>
            <td>
                <Link to={"/messages/" + item.id}>
                    {item.subject !== null && item.subject.length > 0
                        ? item.subject
                        : truncate(unescapeHtml(item.body), 80)}
                </Link>
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

export default withCollectionNavigationProps(MessageList);
