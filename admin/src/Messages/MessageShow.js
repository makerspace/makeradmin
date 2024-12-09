import React, { useEffect, useMemo, useState } from "react";
import { withRouter } from "react-router";
import DateTimeShow from "../Components/DateTimeShow";
import Message from "../Models/Message";

function MessageShow(props) {
    const { id } = props.match.params;
    const messageInstance = useMemo(() => Message.get(id), [id]);

    const [message, setMessage] = useState(() => {
        // Initialize with extracted attributes
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
        // Extract message attributes from the instance and set state
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

        // Call the function once to initialize state
        updateMessage();

        // Subscribe to updates
        const unsubscribe = messageInstance.subscribe(updateMessage);

        // Cleanup subscription on unmount
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

export default withRouter(MessageShow);
