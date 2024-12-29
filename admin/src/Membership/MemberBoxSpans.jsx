import React, { useEffect, useRef, useState } from "react";
import "react-day-picker/lib/style.css";
import { Link, useParams } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateShow from "../Components/DateShow";
import DateTimeShow from "../Components/DateTimeShow";
import Collection from "../Models/Collection";
import { ADD_LABACCESS_DAYS } from "../Models/ProductAction";
import Span from "../Models/Span";
import { get } from "../gateway";
import { confirmModal } from "../message";
import MembershipPeriodsInput from "./MembershipPeriodsInput";

function MemberBoxSpans() {
    const { member_id } = useParams();

    const [, setItems] = useState([]);
    const [pendingLabaccessDays, setPendingLabaccessDays] = useState("?");

    const collectionRef = useRef(
        new Collection({
            type: Span,
            url: `/membership/member/${member_id}/spans`,
            pageSize: 0,
            includeDeleted: true,
        }),
    );

    useEffect(() => {
        get({ url: `/membership/member/${member_id}/pending_actions` }).then(
            (r) => {
                const sum_pending_labaccess_days = r.data.reduce(
                    (acc, value) => {
                        if (value.action.action === ADD_LABACCESS_DAYS)
                            return acc + value.action.value;
                        return acc;
                    },
                    0,
                );
                setPendingLabaccessDays(sum_pending_labaccess_days);
            },
        );
    }, [member_id]);

    useEffect(() => {
        const unsubscribe = collectionRef.current.subscribe(({ items }) => {
            setItems(items);
        });
        return () => {
            unsubscribe();
        };
    }, []);

    const deleteItem = (item) =>
        confirmModal(item.deleteConfirmMessage())
            .then(() => item.del())
            .then(
                () => collectionRef.current.fetch(),
                () => null,
            );

    return (
        <div className="uk-margin-top">
            <h2>Medlemsperioder</h2>
            <p>
                <b>{pendingLabaccessDays}</b> dagar labaccess kommer läggas till
                vid en nyckelsynkronisering.
            </p>
            <hr />
            <MembershipPeriodsInput
                spans={collectionRef.current}
                member_id={member_id}
            />
            <h2>Spans</h2>
            <hr />
            <CollectionTable
                collection={collectionRef.current}
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

export default MemberBoxSpans;
