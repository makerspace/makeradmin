import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Date from "../Components/DateShow";
import DateTimeShow from "../Components/DateTimeShow";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import Span from "../Models/Span";
import { confirmModal } from "../message";

const Row = (deleteItem) => (props) => {
    const { item } = props;
    return (
        <tr>
            <td>
                <Link to={"/membership/spans/" + item.id}>{item.id}</Link>
            </td>
            <td>
                <Link to={"/membership/spans/" + item.id}>{item.type}</Link>
            </td>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>{item.creation_reason}</td>
            <td>
                <DateTimeShow date={item.deleted_at} />
            </td>
            <td>
                <Link to={"/membership/members/" + item.member_id}>
                    #{item.member_number}: {item.firstname} {item.lastname}
                </Link>
            </td>
            <td>
                <Date date={item.startdate} />
            </td>
            <td>
                <Date date={item.enddate} />
            </td>
            <td>
                <a onClick={() => deleteItem(item)} className="removebutton">
                    <i className="uk-icon-trash" />
                </a>
            </td>
        </tr>
    );
};

class SpanList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { page } = this.state;

        this.collection = new Collection({
            type: Span,
            expand: "member",
            includeDeleted: true,
            page,
        });
    }

    render() {
        const deleteItem = (item) =>
            confirmModal(item.deleteConfirmMessage())
                .then(() => item.del())
                .then(
                    () => this.collection.fetch(),
                    () => null,
                );

        const columns = [
            { title: "#", sort: "span_id" },
            { title: "Typ", sort: "type" },
            { title: "Skapad", sort: "created_at" },
            { title: "" },
            { title: "Raderad", sort: "deleted_at" },
            { title: "Medlem", sort: "member_id" },
            { title: "Start", sort: "startdate" },
            { title: "Slut", sort: "enddate" },
        ];

        return (
            <div>
                <h2>Medlemsperioder</h2>
                <CollectionTable
                    rowComponent={Row(deleteItem)}
                    collection={this.collection}
                    columns={columns}
                    onPageNav={this.onPageNav}
                />
            </div>
        );
    }
}

export default SpanList;
