import React from "react";
import "react-day-picker/lib/style.css";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateShow from "../Components/DateShow";
import DateTimeShow from "../Components/DateTimeShow";
import Collection from "../Models/Collection";
import { ADD_LABACCESS_DAYS } from "../Models/ProductAction";
import Span from "../Models/Span";
import { get } from "../gateway";
import { confirmModal } from "../message";
import MembershipPeriodsInput from "./MembershipPeriodsInput";

class MemberBoxSpans extends React.Component {
    constructor(props) {
        super(props);
        this.collection = new Collection({
            type: Span,
            url: `/membership/member/${props.match.params.member_id}/spans`,
            pageSize: 0,
            includeDeleted: true,
        });
        this.state = { items: [], pending_labaccess_days: "?" };
        this.pending_actions = get({
            url: `/membership/member/${props.match.params.member_id}/pending_actions`,
        }).then((r) => {
            const sum_pending_labaccess_days = r.data.reduce((acc, value) => {
                if (value.action.action === ADD_LABACCESS_DAYS)
                    return acc + value.action.value;
                return acc;
            }, 0);
            this.setState({
                pending_labaccess_days: sum_pending_labaccess_days,
            });
        });
    }

    componentDidMount() {
        this.unsubscribe = this.collection.subscribe(({ items }) => {
            this.setState({ items });
        });
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const deleteItem = (item) =>
            confirmModal(item.deleteConfirmMessage())
                .then(() => item.del())
                .then(
                    () => this.collection.fetch(),
                    () => null,
                );

        return (
            <div className="uk-margin-top">
                <h2>Medlemsperioder</h2>
                <p>
                    <b>{this.state.pending_labaccess_days}</b> dagar labaccess
                    kommer läggas till vid en nyckelsynkronisering.
                </p>
                <hr />
                <MembershipPeriodsInput
                    spans={this.collection}
                    member_id={this.props.match.params.member_id}
                />
                <h2>Spans</h2>
                <hr />
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        { title: "#", sort: "span_id" },
                        { title: "Typ", sort: "type" },
                        { title: "Skapad", sort: "created_at" },
                        { title: "" },
                        { title: "Raderad", sort: "deleted_at" },
                        { title: "Start", sort: "startdate" },
                        { title: "Slut", sort: "enddate" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr>
                            <td>
                                <Link to={"/membership/spans/" + item.id}>
                                    {item.id}
                                </Link>
                            </td>
                            <td>
                                <Link to={"/membership/spans/" + item.id}>
                                    {item.type}
                                </Link>
                            </td>
                            <td>
                                <DateTimeShow date={item.created_at} />
                            </td>
                            <td>{item.creation_reason}</td>
                            <td>
                                <DateTimeShow date={item.deleted_at} />
                            </td>
                            <td>
                                <DateShow date={item.startdate} />
                            </td>
                            <td>
                                <DateShow date={item.enddate} />
                            </td>
                            <td>
                                <a
                                    onClick={() => deleteItem(item)}
                                    className="removebutton"
                                >
                                    <i className="uk-icon-trash" />
                                </a>
                            </td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}

export default MemberBoxSpans;
