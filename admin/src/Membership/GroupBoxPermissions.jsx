import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import Permission from "../Models/Permission";
import { get } from "../gateway";

const filterOptions = (items, options) => {
    const current = new Set(items.map((i) => i.id));
    return options.filter((o) => !current.has(o.permission_id));
};

const GroupBoxPermissions = () => {
    const { group_id } = useParams();
    const [selectedOption, setSelectedOption] = useState(null);
    const [options, setOptions] = useState([]);
    const [items, setItems] = useState([]);

    const collection = useMemo(
        () =>
            new Collection({
                type: Permission,
                url: `/membership/group/${group_id}/permissions`,
                idListName: "permissions",
                pageSize: 0,
            }),
        [group_id],
    );

    const options_to_show_in_dropdown = filterOptions(items, options);

    useEffect(() => {
        get({ url: "/membership/permission" }).then(
            ({ data: allPermissions }) => {
                setOptions(allPermissions);
            },
        );
    }, []);

    useEffect(() => {
        const unsubscribe = collection.subscribe(({ items: newItems }) => {
            setItems(newItems);
        });

        return () => {
            unsubscribe();
        };
    }, [collection]);

    const selectOption = (permission) => {
        setSelectedOption(permission);

        if (_.isEmpty(permission)) {
            return;
        }

        collection.add(new Permission(permission)).then(() => {
            setSelectedOption(null);
        });
    };

    const columns = [{ title: "Behörigheter" }];

    const Row = ({ item }) => {
        return (
            <tr>
                <td>{item.permission}</td>
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

    return (
        <div>
            <div className="uk-margin-top uk-form-stacked">
                <label className="uk-form-label" htmlFor="group">
                    Lägg till behörighet
                </label>
                <div className="uk-form-controls">
                    <Select
                        name="group"
                        className="uk-width-1-1"
                        tabIndex={1}
                        options={options_to_show_in_dropdown}
                        value={selectedOption}
                        getOptionValue={(p) => p.permission_id}
                        getOptionLabel={(p) => p.permission}
                        onChange={(permission) => selectOption(permission)}
                        isDisabled={!options_to_show_in_dropdown.length}
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
