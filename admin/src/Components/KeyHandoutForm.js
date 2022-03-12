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
        };
        this.keyCollection = new Collection({type: Key, url: `/membership/member/${member.id}/keys`, idListName: 'keys', pageSize: 0});
    }

    createKey() {
        this.key
            .save()
            .then(() => {
                      this.key.reset({member_id: this.props.member.id});
                      this.keyCollection.fetch();
                  });
    }

    componentDidMount() {
        const {member} = this.props;
        this.unsubscribe_member = member.subscribe(() => this.setState({can_save_member: member.canSave()}));
        this.unsubscribe_keys = this.keyCollection.subscribe((keys) => this.setState({keys: keys}));
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
        const {can_save_member, can_save_key} = this.state;

        return (
        <div className="meep">
            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                        Kontrollera att labbmedlemsavtalet är signerat och säkerställ att rätt medlemsnummer står väl synligt på labbmedlemsavtalet.
                    </div>
                    <fieldset>
                        <input className="uk-checkbox" type="checkbox"/>
                        <label> Signerat labbmedlemsavtal mottaget.</label> 
                    </fieldset>

                </div>

                <div className="uk-section">
                    <div className="uk-container">
                        <h2>2. Kontrollera legitimation</h2>
                        Kontrollera personens legitimation och för in personnummret i fältet nedan. Nyckel kan endast lämnas ut till personen som skall bli medlem.
                    </div>

                    <fieldset>
                        <TextInput model={member} name="civicregno" title="Personnummer" />
                    </fieldset>
                </div>

                <div className="uk-section">
                    <div className="uk-container">
                        <h2>3. Spara information</h2>
                        Spara informationen till databasen 		
                    </div>
                    <div className="uk-container">	
                        <button className="uk-button uk-button-success uk-float-left" tabIndex="3" disabled={!can_save_member}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
                    </div>
                </div>
            </form>

            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); this.createKey(); return false;}}>
                <div className="uk-section">
                    <div className="uk-container">
                        <h2>4. Konfigurera nyckel </h2>
                        Läs av RFID-taggens unika nummer med hjälp av läsaren. 		
                    </div>

                <div className="uk-section"></div>
                    <div className="uk-width-1-1">
                        <TextInput model={this.key} tabIndex="1" name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />
                        <TextInput model={this.key} tabIndex="2" name="description" title="Kommentar" placeholder="Det är valfritt att lägga in en kommentar av nyckeln" />

                        <div className="uk-form-row uk-margin-top">
                            <div className="uk-form-controls">
                                <button className="uk-button uk-button-success uk-float-right" disabled={!can_save_key}><i className="uk-icon-save"/>Skapa nyckel</button>
                            </div>
                        </div>
                    </div>

                    <CollectionTable emptyMessage="Medlemmen har ingen nyckel" rowComponent={Row(this.keyCollection, member.id)} collection={this.keyCollection} columns={[
                        {title: "RFID", sort: "tagid"},
                        {title: "Kommentar"},
                        {title: "Skapad", sort: "created_at"},
                        {title: ""},
                    ]} />
                </div>
            </form>
        </div>
        );
    }
}


export default withRouter(KeyHandoutForm);
