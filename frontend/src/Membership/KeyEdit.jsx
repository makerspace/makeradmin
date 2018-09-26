import React from 'react';
import Key from "../Models/Key";
import TextInput from "../Components/TextInput";
import Textarea from "../Components/Textarea";
import DateTimeInput from "../Components/DateTimeInput";
import {withRouter} from "react-router";
import {confirmModal} from "../message";


class KeyEdit extends React.Component {
    
    constructor(props) {
        super(props);
        const {key_id} = props.params;
        this.key = Key.get(key_id);
        this.state = {saveDisabled: true};
    }
    
    componentDidMount() {
        this.unsubscribe = this.key.subscribe(() => this.setState({saveDisabled: !this.key.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {saveDisabled} = this.state;
        const {router} = this.props;
        
        const onSave = () => this.key.save();
        
        const onDelete = () => {
            return confirmModal(this.key.deleteConfirmMessage())
                .then(() => this.key.del())
                .then(() => {
                    router.push("/membership/keys/");
                })
                .catch(() => null);
        };

        return (
            <div>
                <h2>Redigera RFID-tagg</h2>
                <div className="meep">
                    <form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                        <div className="uk-grid">
                            <div className="uk-width-1-1">
                                <div className="uk-grid">
                                    <div className="uk-width-1-2">
                                        <DateTimeInput model={this.key} name="created_at" title="Skapad" disabled={true} />
                                    </div>
                                    <div className="uk-width-1-2">
                                        <DateTimeInput model={this.key} name="updated_at" title="Ändrad" disabled={true} />
                                    </div>
                                </div>
                                
                                <TextInput model={this.key} name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />
                                <Textarea model={this.key} name="description" title="Kommentar" placeholder="Det är valfritt att lägga in en kommenter av nyckeln" />
                                
                                <div className="uk-form-row uk-margin-top">
                                    <div className="uk-form-controls">
                                        <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Ta bort nyckel</a>
                                        <button className="uk-button uk-button-success uk-float-right" disabled={saveDisabled}><i className="uk-icon-save"/> Spara</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        );
    }
}

export default withRouter(KeyEdit);
