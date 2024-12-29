import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import Permission from "../Models/Permission";
import { get } from "../gateway";

const GroupBoxPermissions = () => {
    const { group_id } = useParams();
    const [showOptions, setShowOptions] = useState([]);
    const [selectedOption, setSelectedOption] = useState(null);
    const [options, setOptions] = useState([]);

    const collectionRef = useRef(
        new Collection({
            type: Permission,
            url: `/membership/group/${group_id}/permissions`,
            idListName: "permissions",
            pageSize: 0,
        }),
    );
    const collection = collectionRef.current;

    const filterOptions = (allOptions) => {
        const existing = new Set((collection.items || []).map((i) => i.id));
        return allOptions.filter(
            (permission) => !existing.has(permission.permission_id),
        );
    };

    useEffect(() => {
        get({ url: "/membership/permission" }).then((data) => {
            const fetchedOptions = data.data;
            setOptions(fetchedOptions);
            setShowOptions(filterOptions(fetchedOptions));
        });

        const unsubscribe = collection.subscribe(() => {
            setShowOptions(filterOptions(options));
        });

        return () => {
            unsubscribe();
        };
    }, []);

    const selectOption = (permission) => {
        setSelectedOption(permission);

        if (_.isEmpty(permission)) {
            return;
        }

        collection.add(new Permission(permission)).then(() => {
            setSelectedOption(null);
            setShowOptions(filterOptions(showOptions));
        });
    };

    const columns = [{ title: "Behörigheter" }];

    const Row = ({ item }) => {
        return (
            <tr>
                <td>{item.permission}</td>
                <td>
                    <a
                        onClick={() => {
                            collection.remove(item).then(() => {
                                setShowOptions(filterOptions(options));
                            });
                        }}
                        className="removebutton"
                    >
                        <i className="uk-icon-trash" />
                    </a>
                </td>
            </tr>
        );
    };

    return (
        <div>
            <div className="uk-margin-top uk-form uk-form-stacked">
                <label className="uk-form-label" htmlFor="group">
                    Lägg till behörighet
                </label>
                <div className="uk-form-controls">
                    <Select
                        name="group"
                        className="uk-select"
                        tabIndex={1}
                        options={showOptions}
                        value={selectedOption}
                        getOptionValue={(p) => p.permission_id}
                        getOptionLabel={(p) => p.permission}
                        onChange={(permission) => selectOption(permission)}
                        isDisabled={!showOptions.length}
                    />
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Gruppen har inga behörigheter"
                    rowComponent={Row}
                    collection={collection}
                    columns={columns}
                />
            </div>
        </div>
    );
};

export default GroupBoxPermissions;
