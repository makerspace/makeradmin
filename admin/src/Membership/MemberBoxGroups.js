import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import Group from "../Models/Group";
import { get } from "../gateway";

const filterOptions = (items, options) => {
    const current = new Set(items.map((i) => i.id));
    return options.filter((o) => !current.has(o.group_id));
};

function MemberBoxGroups() {
    const { member_id } = useParams();
    const collection = useMemo(
        () =>
            new Collection({
                type: Group,
                url: `/membership/member/${member_id}/groups`,
                pageSize: 0,
                idListName: "groups",
            }),
        [member_id],
    );

    const [items, setItems] = useState([]);
    const [options, setOptions] = useState([]);
    const [selectedOption, setSelectedOption] = useState(null);

    useEffect(() => {
        get({ url: "/membership/group" }).then(({ data: updatedOptions }) => {
            setOptions(updatedOptions);
        });
    }, []);

    useEffect(() => {
        const unsubscribe = collection.subscribe(({ items: newItems }) => {
            setItems(newItems || []);
        });

        return () => {
            unsubscribe();
        };
    }, [collection]);

    const selectOption = (group) => {
        setSelectedOption(group);

        if (_.isEmpty(group)) {
            return;
        }

        collection.add(new Group(group)).then(() => {
            setSelectedOption(null);
        });
    };

    const options_to_show_in_dropdown = filterOptions(items, options);

    return (
        <div>
            <div className="uk-margin-top uk-form-stacked">
                <label className="uk-form-label" htmlFor="group">
                    Lägg till i grupp
                </label>
                <div className="uk-form-controls">
                    <Select
                        name="group"
                        className="uk-width-1-1"
                        tabIndex={1}
                        options={options_to_show_in_dropdown}
                        value={selectedOption}
                        getOptionValue={(g) => g.group_id}
                        getOptionLabel={(g) => g.title}
                        onChange={(g) => selectOption(g)}
                    />
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Inte med i några grupper"
                    collection={collection}
                    columns={[
                        { title: "Titel", sort: "title" },
                        { title: "Antal medlemmar" },
                        { title: "" },
                    ]}
                    rowComponent={({ item }) => (
                        <tr>
                            <td>
                                <Link to={`/membership/groups/${item.id}`}>
                                    {item.title}
                                </Link>
                            </td>
                            <td>{item.num_members}</td>
                            <td>
                                <a
                                    onClick={() => collection.remove(item)}
                                    className="removebutton"
                                >
                                    <Icon icon="trash" />
                                </a>
                            </td>
                        </tr>
                    )}
                />
            </div>
        </div>
    );
}

export default MemberBoxGroups;
