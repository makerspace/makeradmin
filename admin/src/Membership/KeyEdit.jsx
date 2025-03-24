import React, { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router";
import DateTimeInput from "../Components/DateTimeInput";
import TextInput from "../Components/TextInput";
import Textarea from "../Components/Textarea";
import Icon from "../Components/icons";
import useModel from "../Hooks/useModel";
import Key from "../Models/Key";
import { browserHistory } from "../browser_history";
import { confirmModal } from "../message";

function KeyEdit() {
    const { key_id } = useParams();
    const key = useModel(Key, key_id);
    const [saveDisabled, setSaveDisabled] = useState(true);

    useEffect(() => {
        const unsubscribe = key.subscribe(() => {
            setSaveDisabled(!key.canSave());
        });

        return () => unsubscribe();
    }, [key]);

    const onSave = useCallback(() => {
        key.save();
    }, [key]);

    const onDelete = useCallback(() => {
        confirmModal(key.deleteConfirmMessage())
            .then(() => key.del())
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
                                        model={key}
                                        name="created_at"
                                        title="Skapad"
                                    />
                                </div>
                                <div className="uk-width-1-2">
                                    <DateTimeInput
                                        model={key}
                                        name="updated_at"
                                        title="Ändrad"
                                    />
                                </div>
                            </div>

                            <TextInput
                                model={key}
                                name="tagid"
                                title="RFID"
                                placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln"
                            />
                            <Textarea
                                model={key}
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
