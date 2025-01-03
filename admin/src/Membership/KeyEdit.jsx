import React, { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router";
import DateTimeInput from "../Components/DateTimeInput";
import TextInput from "../Components/TextInput";
import Textarea from "../Components/Textarea";
import Icon from "../Components/icons";
import Key from "../Models/Key";
import { browserHistory } from "../browser_history";
import { confirmModal } from "../message";

function KeyEdit() {
    const { key_id } = useParams();
    const keyRef = useRef(Key.get(key_id));
    const [saveDisabled, setSaveDisabled] = useState(true);

    useEffect(() => {
        const key = keyRef.current;
        const unsubscribe = key.subscribe(() => {
            setSaveDisabled(!key.canSave());
        });

        return () => unsubscribe();
    }, []);

    const onSave = useCallback(() => {
        keyRef.current.save();
    }, []);

    const onDelete = useCallback(() => {
        confirmModal(keyRef.current.deleteConfirmMessage())
            .then(() => keyRef.current.del())
            .then(() => {
                browserHistory.push("/membership/keys/");
            })
            .catch(() => null);
    }, []);

    return (
        <div>
            <h2>Redigera RFID-tagg</h2>
            <div className="meep">
                <form
                    className="uk-form"
                    onSubmit={(e) => {
                        e.preventDefault();
                        onSave();
                    }}
                >
                    <div className="uk-grid">
                        <div className="uk-width-1-1">
                            <div className="uk-grid">
                                <div className="uk-width-1-2">
                                    <DateTimeInput
                                        model={keyRef.current}
                                        name="created_at"
                                        title="Skapad"
                                    />
                                </div>
                                <div className="uk-width-1-2">
                                    <DateTimeInput
                                        model={keyRef.current}
                                        name="updated_at"
                                        title="Ändrad"
                                    />
                                </div>
                            </div>

                            <TextInput
                                model={keyRef.current}
                                name="tagid"
                                title="RFID"
                                placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln"
                            />
                            <Textarea
                                model={keyRef.current}
                                name="description"
                                title="Kommentar"
                                placeholder="Det är valfritt att lägga in en kommenter av nyckeln"
                            />

                            <div className="form-row uk-margin-top">
                                <div className="uk-form-controls">
                                    <a
                                        className="uk-button uk-button-danger uk-float-left"
                                        onClick={onDelete}
                                    >
                                        <Icon icon="trash" /> Ta bort nyckel
                                    </a>
                                    <button
                                        className="uk-button uk-button-primary uk-float-right"
                                        disabled={saveDisabled}
                                    >
                                        <Icon icon="save" /> Spara
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default KeyEdit;
