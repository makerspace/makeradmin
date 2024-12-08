import React, { useCallback, useEffect, useState } from "react";
import { Async } from "react-select";
import { get } from "../gateway";
import Group from "../Models/Group";
import Member from "../Models/Member";
import Textarea from "./Textarea";
import TextInput from "./TextInput";

const groupOption = (d) => {
    const id = d[Group.model.id];
    const type = "group";
    return {
        id,
        type,
        label: `Grupp: ${d.title}`,
        value: type + id,
    };
};

const memberOption = (d) => {
    const id = d[Member.model.id];
    const type = "member";
    const lastname = d.lastname || "";
    return {
        id,
        type,
        label: `Medlem: ${d.firstname} ${lastname} (#${d.member_number})`,
        value: type + id,
    };
};

const MessageForm = ({ message, onSave, recipientSelect }) => {
    const [sendDisabled, setSendDisabled] = useState(true);
    const [recipients, setRecipients] = useState([]);
    const [bodyLength, setBodyLength] = useState(message.body.length);

    useEffect(() => {
        const unsubscribe = message.subscribe(() => {
            setSendDisabled(!message.canSave());
            setRecipients(message.recipients);
            setBodyLength(message.body.length); // Update body length whenever the message updates
        });

        return () => {
            unsubscribe();
        };
    }, [message]);

    const loadOptions = useCallback((inputValue, callback) => {
        Promise.all([
            get({
                url: "/membership/group",
                params: {
                    search: inputValue,
                    sort_by: "name",
                    sort_order: "asc",
                },
            }),
            get({
                url: "/membership/member",
                params: {
                    search: inputValue,
                    sort_by: "firstname",
                    sort_order: "asc",
                },
            }),
        ]).then(([{ data: groups }, { data: members }]) =>
            callback(
                groups
                    .map((d) => groupOption(d))
                    .concat(members.map((d) => memberOption(d))),
            ),
        );
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave();
    };

    return (
        <form className="uk-form uk-form-horizontal" onSubmit={handleSubmit}>
            {recipientSelect && (
                <div className="uk-form-row">
                    <label className="uk-form-label" htmlFor="recipient">
                        Mottagare
                    </label>
                    <div className="uk-form-controls">
                        <Async
                            name="recipients"
                            isMulti
                            cache={false}
                            placeholder="Type to search for member or group"
                            getOptionValue={(e) => e.value}
                            getOptionLabel={(e) => e.label}
                            loadOptions={loadOptions}
                            value={recipients}
                            onChange={(values) => {
                                message.recipients = values;
                                setRecipients(values);
                            }}
                        />
                    </div>
                </div>
            )}

            <TextInput
                model={message}
                name="subject"
                title="Ärende"
                onChange={() => setBodyLength(message.body.length)} // Ensure the length is updated when body changes
            />
            <Textarea
                model={message}
                name="body"
                title="Meddelande"
                onChange={() => setBodyLength(message.body.length)} // Ensure the length is updated when body changes
            />

            <div className="uk-form-row">
                <div className="uk-form-controls">
                    <p className="uk-float-left">
                        <span id="characterCounter">{bodyLength}</span> tecken
                    </p>
                </div>
                <div className="uk-form-controls">
                    <button
                        className="uk-button uk-button-success uk-float-right"
                        disabled={sendDisabled}
                    >
                        <i className="uk-icon-save" /> Skicka
                    </button>
                </div>
            </div>
        </form>
    );
};

export default MessageForm;
