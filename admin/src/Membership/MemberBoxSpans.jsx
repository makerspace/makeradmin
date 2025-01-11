import React, { useEffect, useMemo, useState } from "react";
import "react-day-picker/lib/style.css";
import { Link, useParams } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateShow from "../Components/DateShow";
import DateTimeShow from "../Components/DateTimeShow";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import { ADD_LABACCESS_DAYS } from "../Models/ProductAction";
import Span from "../Models/Span";
import { get } from "../gateway";
import { confirmModal } from "../message";
import MembershipPeriodsInput from "./MembershipPeriodsInput";

const empty_title_with_nonzero_width = <>&nbsp;&nbsp;&nbsp;&nbsp;</>;

function MemberBoxSpans() {
    const { member_id } = useParams();
    const [pendingLabaccessDays, setPendingLabaccessDays] = useState("?");

    const collection = useMemo(
        () =>
            new Collection({
                type: Span,
                url: `/membership/member/${member_id}/spans`,
                pageSize: 0,
                includeDeleted: true,
            }),
        [member_id],
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

    const deleteItem = (item) =>
        confirmModal(item.deleteConfirmMessage())
            .then(() => item.del())
            .then(
                () => collection.fetch(),
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
            <MembershipPeriodsInput spans={collection} member_id={member_id} />
            <h2>Spans</h2>
            <hr />
            <CollectionTable
                collection={collection}
                columns={[
                    { title: "#", sort: "span_id" },
                    { title: "Typ", sort: "type" },
                    { title: "Skapad", sort: "created_at" },
                    { title: "Ursprung" },
                    { title: "Raderad", sort: "deleted_at" },
                    { title: "Start", sort: "startdate" },
                    { title: "Slut", sort: "enddate" },
                    { title: empty_title_with_nonzero_width },
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
                            {item.deleted_at === null && (
                                <a
                                    onClick={() => deleteItem(item)}
                                    className="removebutton"
                                >
                                    <Icon icon="trash" />
                                </a>
                            )}
                        </td>
                    </tr>
                )}
            />
        </div>
    );
}

export default MemberBoxSpans;
