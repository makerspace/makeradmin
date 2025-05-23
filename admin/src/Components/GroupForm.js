import React, { useEffect, useState } from "react";
import DateTimeInput from "./DateTimeInput";
import TextInput from "./TextInput";
import Textarea from "./Textarea";
import Icon from "./icons";

const GroupForm = ({ group, onSave, onDelete }) => {
    const [saveDisabled, setSaveDisabled] = useState(true);

    useEffect(() => {
        const unsubscribe = group.subscribe(() => {
            setSaveDisabled(!group.canSave());
        });

        return () => {
            unsubscribe();
        };
    }, [group]);

    return (
        <div className="meep">
            <form
                className="uk-margin-bottom"
                onSubmit={(e) => {
                    e.preventDefault();
                    onSave();
                }}
            >
                <TextInput model={group} name="name" title="Namn" />
                <TextInput
                    model={group}
                    name="title"
                    title="Titel"
                    icon="tag"
                />
                <Textarea
                    model={group}
                    name="description"
                    title="Beskrivning"
                />
                <DateTimeInput model={group} name="created_at" title="Skapad" />
                <DateTimeInput
                    model={group}
                    name="updated_at"
                    title="Uppdaterad"
                />
                <DateTimeInput
                    model={group}
                    name="deleted_at"
                    title="Borttagen"
                />

                <div className="form-row uk-margin-top">
                    <div className="uk-form-controls">
                        {group.id && !group.deleted_at && (
                            <a
                                className="uk-button uk-button-danger uk-float-left"
                                onClick={onDelete}
                            >
                                <Icon icon="trash" /> Ta bort grupp
                            </a>
                        )}
                        <button
                            className="uk-button uk-button-primary uk-float-right"
                            disabled={saveDisabled}
                        >
                            <Icon icon="save" /> {group.id ? "Spara" : "Skapa"}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
};

export default GroupForm;
