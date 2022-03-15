import React from 'react';
import DateTimeShow from "./DateTimeShow";
import TextInput from "./TextInput";
import {withRouter} from "react-router";
import {Row} from "../Membership/MemberBoxKeys"
import Key from "../Models/Key"
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";


class KeyHandoutForm extends React.Component {

    constructor(props) {
        super(props);
        const {member} = this.props;
        this.key = new Key({member_id: member.id});
        this.state = {
            can_save_member: false,
            can_save_key: false,
            keys: [],
            has_signed: false,
        };
        this.keyCollection = new Collection({type: Key, url: `/membership/member/${member.id}/keys`, idListName: 'keys', pageSize: 0});
        this.signedChanged = this.signedChanged.bind(this);
    }

    createKey() {
        this.key
            .save()
            .then(() => {
                      this.key.reset({member_id: this.props.member.id});
                      this.keyCollection.fetch();
                  });
    }

    signedChanged(signed) {
        this.setState({has_signed: signed});
    }

    componentDidMount() {
        const {member} = this.props;
        this.unsubscribe_member = member.subscribe(() => this.setState({can_save_member: member.canSave(), has_signed: (member.civicregno && member.civicregno.length > 0) ? true : false}));
        this.unsubscribe_keys = this.keyCollection.subscribe((keys) => this.setState({keys: keys.items}));
        const key = this.key;
        this.unsubscribe_key = key.subscribe(() => this.setState({can_save_key: key.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe_member();
        this.unsubscribe_keys();
        this.unsubscribe_key();
    }

    render() {
        const {member, onSave, onDelete} = this.props;
        const {can_save_member, can_save_key, keys, has_signed} = this.state;

        // Show different content based on if the user has a key or not
        let key_paragraph;
        if (keys.length === 0) {
            key_paragraph = <>
                    <div className="uk-container">
                        <TextInput model={this.key} tabIndex="1" name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />

                        <div className="uk-form-row uk-margin-top">
                            <div className="uk-form-controls">
                                <button className="uk-button uk-button-success uk-float-right" disabled={!can_save_key}><i className="uk-icon-save"/> Skapa nyckel</button>
                            </div>
                        </div>
                    </div>
                </>;
        } else if (keys.length === 1) {
            key_paragraph = <>
                    <div className="uk-container">
                        Användaren har en nyckel registrerad (med id=<span style={{fontFamily: "monospace"}}>{keys[0].tagid}</span>). Kontrollera om hen vet om det och har kvar nyckeln. Gå annars till <a href={"/membership/members/" + member.id + "/keys"}>Nycklar</a> och ta bort den gamla nyckeln, och lägg till en ny.
                    </div>
                </>;
        } else {
            key_paragraph = <>
                <div className="uk-container">
                    <div className="uk-container">
                        Användaren har flera nycklar registrerade! Gå till <a href={"/membership/members/" + member.id + "/keys"}>Nycklar</a> och ta bort alla nycklar utom en.
                    </div>
                </div>
            </>;
        }

        // Section 2 and onward shall only be visible after lab contract has been signed
        const section2andon = <>
            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>2. Kontrollera legitimation</h2>
                        Kontrollera personens legitimation och för in personnummret i fältet nedan. Nyckel kan endast lämnas ut till personen som skall bli medlem.
                    </div>

                    <fieldset>
                        <TextInput model={member} name="civicregno" title="Personnummer" />
                        <div className="uk-container">
                            <button className="uk-button uk-button-success uk-float-right" tabIndex="3" disabled={!can_save_member}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
                        </div>
                    </fieldset>
                </div>
            </form>

            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); this.createKey(); return false;}}>
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>3. Kontrollera nyckel </h2>		
                    </div>
                    {key_paragraph}
                </div>
            </form>
        </>;

        return (
        <div className="meep">
            <div className="uk-form">
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                        Kontrollera att labbmedlemsavtalet är signerat och säkerställ att rätt medlemsnummer står väl synligt på labbmedlemsavtalet.
                    </div>
                    <br/>
                    <fieldset>
                        <input className="uk-checkbox" type="checkbox" checked={has_signed} onChange={(e) => this.signedChanged(e.target.checked)}/>
                        <label> Signerat labbmedlemsavtal mottaget.</label> 
                    </fieldset>
                </div>
            </div>

            {has_signed ? section2andon : ""}
        </div>
        );
    }
}


export default withRouter(KeyHandoutForm);
