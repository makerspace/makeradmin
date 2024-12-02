import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import Group from "../Models/Group";

const filterOptions = (items, options) => {
    const current = new Set(items.map((i) => i.id));
    return options.filter((o) => !current.has(o.group_id));
};

function MemberBoxGroups(props) {
    const collectionRef = useRef(
        new Collection({
            type: Group,
            url: `/membership/member/${props.match.params.member_id}/groups`,
            idListName: "groups",
            pageSize: 0,
        }),
    );

    const [items, setItems] = useState([]);
    const [options, setOptions] = useState([]);
    const [showOptions, setShowOptions] = useState([]);
    const [selectedOption, setSelectedOption] = useState(null);

    useEffect(() => {
        get({ url: "/membership/group" }).then((data) => {
            const updatedOptions = data.data;
            setOptions(updatedOptions);
            setShowOptions(filterOptions(items, updatedOptions));
        });

        const unsubscribe = collectionRef.current.subscribe(
            ({ items: newItems }) => {
                setItems(newItems || []);
                setShowOptions(filterOptions(newItems || [], options));
            },
        );

        return () => {
            unsubscribe();
        };
    }, []);

    const selectOption = (group) => {
        setSelectedOption(group);

        if (_.isEmpty(group)) {
            return;
        }

        collectionRef.current.add(new Group(group)).then(() => {
            setSelectedOption(null);
            const updatedItems = [...items, { id: group.group_id }];
            setShowOptions(filterOptions(updatedItems, options));
        });
    };

    return (
        <div>
            <div className="uk-margin-top uk-form uk-form-stacked">
                <label className="uk-form-label" htmlFor="group">
                    Lägg till i grupp
                </label>
                <div className="uk-form-controls">
                    <Select
                        name="group"
                        className="uk-select"
                        tabIndex={1}
                        options={showOptions}
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
                    collection={collectionRef.current}
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
                                    onClick={() =>
                                        collectionRef.current
                                            .remove(item)
                                            .then(() => {
                                                const updatedItems =
                                                    items.filter(
                                                        (i) => i.id !== item.id,
                                                    );
                                                setItems(updatedItems);
                                                setShowOptions(
                                                    filterOptions(
                                                        updatedItems,
                                                        options,
                                                    ),
                                                );
                                            })
                                    }
                                    className="removebutton"
                                >
                                    <i className="uk-icon-trash" />
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
