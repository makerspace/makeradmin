import React from 'react';
import TextInput from "./TextInput";
import {withRouter} from "react-router";
import Key from "../Models/Key"
import Collection from "../Models/Collection";


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
        this.onSave = this.onSave.bind(this);
    }

    onSave() {
        console.log("onSave");
        console.log(this.key);
        console.log(this.key.isDirty());
        console.log(this.key.canSave());
        if (this.key && this.key.isDirty() && this.key.canSave()) {
            this.key
                .save()
                .then(() => {
                            this.key.reset({member_id: this.props.member.id});
                            this.keyCollection.fetch();
                        });
        }

        const {member} = this.props;
        console.log(member);
        console.log(member.isDirty());
        console.log(member.canSave());
        if (member.isDirty() && member.canSave()) {
            member.save();
        }
    }

    signedChanged(signed) {
        this.setState({has_signed: signed});
    }

    componentDidMount() {
        const {member} = this.props;
        member.initialization(() => this.setState({has_signed: (member.civicregno && member.civicregno.length > 0) ? true : false}));
        this.unsubscribe_member = member.subscribe(() => this.setState({can_save_member: member.canSave()}));
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
        const {member, onDelete} = this.props;
        const {can_save_member, can_save_key, keys, has_signed} = this.state;

        // Show different content based on if the user has a key or not
        let key_paragraph;
        if (keys.length === 0) {
            key_paragraph = <>
                    <div className="uk-container">
                        Skapa en ny nyckel genom att läsa in den i fältet nedan.
                        <TextInput model={this.key} tabIndex="1" name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />
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
            <div className="uk-section">
                <div className="uk-container">
                    <h2>2. Kontrollera legitimation</h2>
                    Kontrollera personens legitimation och för in personnummret i fältet nedan. Nyckel kan endast lämnas ut till personen som skall bli medlem.
                </div>

                <fieldset>
                    <TextInput model={member} tabIndex="1" name="civicregno" title="Personnummer" pattern="([0-9]{2})?[0-9]{6}-?[0-9]{4}" placeholder="YYYYMMDD-XXXX" />
                </fieldset>
            </div>

            <div className="uk-section">
                <div className="uk-container">
                    <h2>3. Övrig information</h2>
                    Kontrollera <b>epost</b> så personen kommer åt kontot, och <b>telefon</b> så vi kan nå hen när det är mer brådskande.
                </div>
                <fieldset>
                    <TextInput model={member} name="email" tabIndex="1" type="email" title="Epost" />
                    <TextInput model={member} name="phone" tabIndex="1" type="phone" title="Telefonnummer" />
                </fieldset>
            </div>

            <div className="uk-section">
                <div className="uk-container">
                    <h2>4. Kontrollera nyckel </h2>
                </div>
                {key_paragraph}
            </div>
        </>;

        return (
        <div className="meep">
            <div className="uk-form" onSubmit={(e) => {e.preventDefault(); this.onSave(); return false;}}>
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                        Kontrollera att labbmedlemsavtalet är signerat och säkerställ att rätt medlemsnummer står väl synligt på labbmedlemsavtalet.
                    </div>
                    <br/>
                    <fieldset>
                        <input className="uk-checkbox" type="checkbox" tabIndex="1" checked={has_signed} onChange={(e) => this.signedChanged(e.target.checked)}/>
                        <label> Signerat labbmedlemsavtal mottaget.</label> 
                    </fieldset>
                </div>

                {has_signed ? section2andon : ""}

                <div className="uk-container">
                    <button className="uk-button uk-button-success uk-float-right" tabIndex="1" disabled={!can_save_member && !can_save_key}><i className="uk-icon-save"/> Spara</button>
                </div>
            </div>
        </div>
        );
    }
}


export default withRouter(KeyHandoutForm);
