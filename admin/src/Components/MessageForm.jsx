import React from 'react';
import { withRouter } from 'react-router';
import TextInput from "./TextInput";
import Textarea from "./Textarea";
import {Async} from "react-select";
import { get } from "../gateway";
import Group from "../Models/Group";
import Member from "../Models/Member";


const groupOption = d => {
    const id = d[Group.model.id];
    const type = "group";
    return {
        id,
        type,
        label: `Grupp: ${d.title}`,
        value: type + id,
    };
};

const memberOption = d => {
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

class MessageForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            messageType: null,
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {message} = this.props;
        this.unsubscribe = message.subscribe(() => {
            this.setState({
                              sendDisabled: !message.canSave(),
                              recipients: message.recipients,
                          });
        });
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    loadOptions(inputValue, callback) {
        Promise.all([
                        get({url: '/membership/group', params: {search: inputValue, sort_by: "name", sort_order: "asc"}}),
                        get({url: '/membership/member', params: {search: inputValue, sort_by: "firstname", sort_order: "asc"}}),
                    ])
               .then(([{data: groups}, {data: members}]) => callback(groups.map(d => groupOption(d)).concat(members.map(d => memberOption(d)))));
    }
    
    render() {
        
        
        const {message, onSave: onSend, recipientSelect} = this.props;
        const {sendDisabled, recipients} = this.state;
        
        return (
            <form className="uk-form uk-form-horizontal" onSubmit={(e) => {e.preventDefault(); onSend(); return false;}}>
                {
                    recipientSelect
                    ?
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
                                   getOptionValue={e => e.value}
                                   getOptionLabel={e => e.label}
                                   loadOptions={(v, c) => this.loadOptions(v, c)}
                                   value={recipients}
                                   onChange={values => message.recipients = values}
                            />
                        </div>
                    </div>
                    :
                    ""
                }

                <TextInput model={message} name="subject" title="Ärende"/>
                <Textarea model={message} name="body" title="Meddelande"/>

                <div className="uk-form-row">
                    <div className="uk-form-controls">
                        <p className="uk-float-left"><span id="characterCounter">{message.body.length}</span> tecken</p>
                    </div>
                    <div className="uk-form-controls">
                        <button className="uk-button uk-button-success uk-float-right" disabled={sendDisabled}><i className="uk-icon-save"/> Skicka</button>
                    </div>
                </div>
            </form>
        );
    }
}


export default withRouter(MessageForm);
