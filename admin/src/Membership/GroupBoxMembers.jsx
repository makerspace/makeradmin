import React, { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Async } from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Date from "../Components/DateShow";
import Icon from "../Components/icons";
import { get } from "../gateway";
import Collection from "../Models/Collection";
import Member from "../Models/Member";

const Row = (collection) => (props) => {
    const { item } = props;
    return (
        <tr>
            <td>
                <Link to={"/membership/members/" + item.id}>
                    {item.member_number}
                </Link>
            </td>
            <td>{item.firstname}</td>
            <td>{item.lastname}</td>
            <td>{item.email}</td>
            <td>
                <Date date={item.created_at} />
            </td>
            <td>
                <a
                    onClick={() => collection.remove(item)}
                    className="removebutton"
                >
                    <Icon icon="trash" />
                </a>
            </td>
        </tr>
    );
};

export default function GroupBoxMembers() {
    const { group_id } = useParams();
    const [selectedOption, setSelectedOption] = useState(null);

    const collection = React.useMemo(
        () =>
            new Collection({
                type: Member,
                url: `/membership/group/${group_id}/members`,
                idListName: "members",
            }),
        [group_id],
    );

    const loadOptions = useCallback((inputValue, callback) => {
        get({
            url: "/membership/member",
            params: {
                search: inputValue,
                sort_by: "firstname",
                sort_order: "asc",
            },
        }).then((data) => callback(data.data));
    }, []);

    const selectOption = useCallback(
        (member) => {
            setSelectedOption(member);

            if (_.isEmpty(member)) {
                return;
            }

            collection
                .add(new Member(member))
                .then(() => setSelectedOption(null));
        },
        [collection],
    );

    const columns = [
        { title: "#", sort: "member_id" },
        { title: "Förnamn", sort: "firstname" },
        { title: "Efternamn", sort: "lastname" },
        { title: "E-post", sort: "email" },
        { title: "Blev medlem", sort: "created_at" },
        { title: "" },
    ];

    return (
        <div>
            <div className="uk-margin-top uk-form-stacked">
                <label className="uk-form-label" htmlFor="member">
                    Lägg till i grupp
                </label>
                <div className="uk-form-controls">
                    <Async
                        name="member"
                        tabIndex={1}
                        placeholder="Type to search for member"
                        value={selectedOption}
                        getOptionValue={(m) => m.member_id}
                        getOptionLabel={(m) =>
                            "#" +
                            m.member_number +
                            ": " +
                            m.firstname +
                            " " +
                            (m.lastname || "") +
                            " <" +
                            m.email +
                            ">"
                        }
                        loadOptions={loadOptions}
                        onChange={selectOption}
                    />
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Inga medlemmar i grupp"
                    rowComponent={Row(collection)}
                    collection={collection}
                    columns={columns}
                />
            </div>
        </div>
    );
}
