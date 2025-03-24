import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import TextInput from "../Components/TextInput";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import Key from "../Models/Key";
import { confirmModal } from "../message";

const Row = (collection) => (props) => {
    const { item } = props;

    const deleteKey = () => {
        return confirmModal(item.deleteConfirmMessage())
            .then(() => item.del())
            .then(
                () => collection.fetch(),
                () => null,
            );
    };

    return (
        <tr>
            <td>
                <Link to={"/membership/keys/" + item.id}>{item.tagid}</Link>
            </td>
            <td>{item.description}</td>
            <td>
                <DateTimeShow date={item.created_at} />
            </td>
            <td>
                <a onClick={deleteKey} className="removebutton">
                    <Icon icon="trash" />
                </a>
            </td>
        </tr>
    );
};

function MemberBoxKeys() {
    const { member_id } = useParams();

    const collection = useMemo(
        () =>
            new Collection({
                type: Key,
                url: `/membership/member/${member_id}/keys`,
                idListName: "keys",
                pageSize: 0,
            }),
        [member_id],
    );

    const [key, setKey] = useState(new Key({ member_id }));
    const [saveEnabled, setSaveEnabled] = useState(false);

    useEffect(() => {
        const unsubscribe = key.subscribe(() => {
            setSaveEnabled(key.canSave());
        });

        return () => {
            unsubscribe();
        };
    }, [key]);

    const createKey = () => {
        key.save().then(() => {
            const newKey = new Key({ member_id: member_id });
            setKey(newKey);
            collection.fetch();
        });
    };

    const columns = [
        { title: "RFID", sort: "tagid" },
        { title: "Kommentar" },
        { title: "Skapad", sort: "created_at" },
        { title: "" },
    ];

    return (
        <div>
            <div className="uk-margin-top">
                <div className="meep">
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            createKey();
                        }}
                    >
                        <div className="uk-grid">
                            <div className="uk-width-1-1">
                                <TextInput
                                    model={key}
                                    tabIndex="1"
                                    name="tagid"
                                    title="RFID"
                                    placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln"
                                />
                                <TextInput
                                    model={key}
                                    tabIndex="2"
                                    name="description"
                                    title="Kommentar"
                                    placeholder="Det är valfritt att lägga in en kommentar av nyckeln"
                                />

                                <div className="uk-margin-top">
                                    <div className="uk-form-controls">
                                        <button
                                            className="uk-button uk-button-primary uk-float-right"
                                            disabled={!saveEnabled}
                                        >
                                            <Icon icon="save" /> Skapa nyckel
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Inga nycklar för medlemmen"
                    rowComponent={Row(collection, member_id)}
                    collection={collection}
                    columns={columns}
                />
            </div>
        </div>
    );
}

export default MemberBoxKeys;
