import React, { useEffect, useMemo, useState } from "react";
import DateTimeShow from "../Components/DateTimeShow";
import Message from "../Models/Message";

function MessageShow(props) {
    const { id } = props.match.params;
    const messageInstance = useMemo(() => Message.get(id), [id]);

    const [message, setMessage] = useState(() => {
        return {
            body: "",
            created_at: null,
            id: null,
            recipient: "",
            recipient_id: null,
            recipients: [],
            sent_at: null,
            status: "",
            subject: "",
            template: "",
            updated_at: null,
        };
    });

    useEffect(() => {
        const updateMessage = () => {
            setMessage({
                body: messageInstance.body,
                created_at: messageInstance.created_at,
                id: messageInstance.id,
                recipient: messageInstance.recipient,
                recipient_id: messageInstance.recipient_id,
                recipients: messageInstance.recipients,
                sent_at: messageInstance.sent_at,
                status: messageInstance.status,
                subject: messageInstance.subject,
                template: messageInstance.template,
                updated_at: messageInstance.updated_at,
            });
        };

        updateMessage();

        const unsubscribe = messageInstance.subscribe(updateMessage);

        return () => {
            unsubscribe();
        };
    }, [messageInstance]);

    return (
        <div className="uk-margin-top">
            <h2>Utskick</h2>
            <div className="uk-panel uk-panel-box uk-margin-bottom">
                <table>
                    <tbody>
                        <tr>
                            <th align="left">Created</th>
                            <td>
                                <DateTimeShow
                                    date={message.created_at || null}
                                />
                            </td>
                        </tr>
                        <tr>
                            <th align="left">Status</th>
                            <td>{Message.statusText(message)}</td>
                        </tr>
                        <tr>
                            <th align="left">Sent</th>
                            <td>
                                <DateTimeShow date={message.sent_at || null} />
                            </td>
                        </tr>
                        <tr>
                            <th align="left">Recipient</th>
                            <td>{message.recipient || "N/A"}</td>
                        </tr>
                        <tr>
                            <th align="left">Template Used</th>
                            <td>{message.template || "N/A"}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div className="uk-panel uk-panel-box uk-margin-bottom">
                <h3
                    className="uk-panel-title"
                    dangerouslySetInnerHTML={{ __html: message.subject || "" }}
                />
            </div>
            <div className="uk-panel uk-panel-box uk-margin-bottom">
                <div dangerouslySetInnerHTML={{ __html: message.body || "" }} />
            </div>
        </div>
    );
}

export default MessageShow;
