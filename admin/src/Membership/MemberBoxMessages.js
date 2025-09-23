import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import { withCollectionNavigationProps } from "../Models/CollectionNavigation";
import Message from "../Models/Message";

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

class MemberBoxMessages extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;
        this.collection = new Collection({
            type: Message,
            url:
                "/messages/member/" +
                props.match.params.member_id +
                "/messages",
            search,
            page,
        });
    }

    render() {
        const columns = [
            { title: "Skapad", sort: "created_at" },
            { title: "Status", sort: "status" },
            { title: "Mottagare", sort: "recipient" },
            { title: "Meddelande", sort: "subject" },
        ];

        return (
            <div className="uk-margin-top">
                <CollectionTable
                    rowComponent={Row}
                    collection={this.collection}
                    columns={columns}
                    onPageNav={this.onPageNav}
                />
                <Link
                    to={
                        "/membership/members/" +
                        this.props.match.params.member_id +
                        "/messages/new"
                    }
                    className="uk-button uk-button-primary"
                >
                    <Icon icon="mail" /> Skicka meddelande
                </Link>
            </div>
        );
    }
}

export default withCollectionNavigationProps(MemberBoxMessages);
