import Message from "Models/Message";
import React, { useEffect, useState } from "react";
import Async from "react-select/async";
import { get } from "../gateway";
import Group from "../Models/Group";
import Member from "../Models/Member";
import Icon from "./icons";
import Textarea from "./Textarea";
import TextInput from "./TextInput";

type GroupOption = {
    id: number;
    type: "group";
    label: string;
    value: string;
};

const groupOption = (d: Group): GroupOption => {
    const id = d.id;
    const type = "group";
    return {
        id: id!,
        type,
        label: `Grupp: ${d.title}`,
        value: type + id,
    };
};

type MemberOption = {
    id: number;
    type: "member";
    label: string;
    value: string;
};

type CombinedOption = {
    type: "combined";
    label: string;
    value: string;
    inner: (MemberOption | GroupOption)[];
};

const memberOption = (d: Member): MemberOption => {
    const id = d.member_id;
    const type = "member";
    const lastname = d.lastname || "";
    return {
        id,
        type,
        label: `Medlem: ${d.firstname} ${lastname} (#${d.member_number})`,
        value: type + id,
    };
};

const MessageForm = ({
    message,
    onSave,
    recipientSelect,
}: {
    message: Message;
    onSave: () => void;
    recipientSelect: boolean;
}) => {
    const [sendDisabled, setSendDisabled] = useState(true);
    const [recipients, setRecipients] = useState<
        (MemberOption | GroupOption)[]
    >([]);
    const [bodyLength, setBodyLength] = useState(message.body.length);
    const memberCache = React.useRef(new Map<number, Member>()).current;

    const getMember = async (id: number): Promise<Member> => {
        if (memberCache.has(id)) {
            return memberCache.get(id)!;
        }
        const { data } = await get({ url: `/membership/member/${id}` });
        memberCache.set(id, data);
        return data;
    };

    useEffect(() => {
        const unsubscribe = message.subscribe(() => {
            setSendDisabled(!message.canSave());
            setRecipients(
                message.recipients as any as (MemberOption | GroupOption)[],
            );
            setBodyLength(message.body.length);
        });

        return () => {
            unsubscribe();
        };
    }, [message]);

    const loadOptions = (
        inputValue: string,
        callback: (
            options: (MemberOption | GroupOption | CombinedOption)[],
        ) => void,
    ) => {
        const intListMatch = inputValue.match(/^(\d+[\s,]*)+$/);
        if (intListMatch) {
            const ids = inputValue
                .split(/[\s,]+/)
                .map((v) => parseInt(v, 10))
                .filter((v) => !isNaN(v));
            if (ids.length > 0) {
                Promise.all(ids.map(getMember)).then((members) => {
                    const options = members.map(memberOption);
                    callback([
                        {
                            type: "combined",
                            label: `${options.map((o) => o.label).join(", ")}`,
                            value: "combined-" + ids.join("-"),
                            inner: options,
                        },
                    ]);
                });
                return;
            }
        }

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
        ]).then(
            ([{ data: groups }, { data: members }]: [
                { data: Group[] },
                { data: Member[] },
            ]) =>
                callback(
                    groups
                        .map(
                            (d) => groupOption(d) as GroupOption | MemberOption,
                        )
                        .concat(members.map((d) => memberOption(d))),
                ),
        );
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        onSave();
    };

    return (
        <form className="uk-form-horizontal" onSubmit={handleSubmit}>
            {recipientSelect && (
                <div className="form-row">
                    <label className="uk-form-label" htmlFor="recipient">
                        Mottagare
                    </label>
                    <div className="uk-form-controls">
                        <Async<
                            MemberOption | GroupOption | CombinedOption,
                            true
                        >
                            name="recipients"
                            isMulti
                            placeholder="Type to search for member or group"
                            getOptionValue={(e) => e.value}
                            getOptionLabel={(e) => e.label}
                            loadOptions={loadOptions}
                            value={recipients}
                            onChange={(values) => {
                                const flattened = values.flatMap((v) =>
                                    v.type === "combined" ? v.inner : v,
                                );
                                message.recipients = flattened;
                                setRecipients(flattened);
                            }}
                        />
                    </div>
                </div>
            )}

            <TextInput
                model={message}
                name="subject"
                title="Ärende"
                onChange={() => setBodyLength(message.body.length)}
            />
            <Textarea
                model={message}
                name="body"
                title="Meddelande"
                onChange={() => setBodyLength(message.body.length)}
            />

            <div className="form-row">
                <div className="uk-form-controls">
                    <p className="uk-float-left">
                        <span id="characterCounter">{bodyLength}</span> tecken
                    </p>
                </div>
                <div className="uk-form-controls">
                    <button
                        className="uk-button uk-button-primary uk-float-right"
                        disabled={sendDisabled}
                    >
                        <Icon icon="send" /> Skicka
                    </button>
                </div>
            </div>
        </form>
    );
};

export default MessageForm;
