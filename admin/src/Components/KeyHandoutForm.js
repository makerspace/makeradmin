import React from 'react';
import TextInput from "./TextInput";
import {withRouter} from "react-router";
import Key from "../Models/Key"
import Span from "../Models/Span"
import {filterCategory} from '../Models/Span';
import Collection from "../Models/Collection";
import {ADD_LABACCESS_DAYS} from "../Models/ProductAction";
import {utcToday, parseUtcDate} from "../utils";


function last_span_enddate(spans, category) {
    const last_span = filterCategory(spans, category).splice(-1)[0];
    if (last_span) {
        return last_span.enddate;
    }
    return null;
}

function DateView(props) {
    const is_valid = props.date && parseUtcDate(props.date) < utcToday();
    let status, text;

    if (!props.date) {
        status = <div className="uk-panel-badge uk-badge uk-badge-warning">Saknas</div>;
        text = <p style={{"color": "gray", "fontStyle": "italic"}}>{props.placeholder}</p>;
    } else if (!is_valid) {
        status = <div className="uk-panel-badge uk-badge uk-badge-danger">Utgånget</div>;
        text = <p>Giltigt till: <span style={{"color": "red", "fontStyle": "italic"}}>{props.date}</span></p>;
    } else {
        status = <div className="uk-panel-badge uk-badge uk-badge-success">OK</div>;
        text = <p>Giltigt till: {props.date}</p>;
    }

    // Override if there are pending days to be synchronized
    if (props.pending || is_valid) {
        status = <div className="uk-panel-badge uk-badge uk-badge-success">OK</div>;
    }

    return <div className="uk-panel uk-panel-box">
        <h4>{props.title}</h4>
        {status}
        {text}
        { props.pending ? <p><span>(<b>{props.pending}</b> dagar kommer läggas till vid en nyckelsynkronisering)</span></p> : null }
    </div>
}


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
            pending_labaccess_days: "?",
            labaccess_enddate: "",
            membership_enddate: "",
            special_enddate: "",
        };
        this.unsubscribe = [];
        this.keyCollection = new Collection({type: Key, url: `/membership/member/${member.id}/keys`, idListName: 'keys', pageSize: 0});
        this.spanCollection = new Collection({type: Span, url: `/membership/member/${member.id}/spans`, pageSize: 0});
        this.signedChanged = this.signedChanged.bind(this);
        this.onSave = this.onSave.bind(this);
        get({url: `/membership/member/${member.id}/pending_actions`}).then((r) => {
            const sum_pending_labaccess_days = r.data.reduce((acc, value) => {
            if (value.action.action === ADD_LABACCESS_DAYS)
                return acc + value.action.value;
            return acc;
            }, 0);
            this.setState({pending_labaccess_days: sum_pending_labaccess_days});
        });
    }

    onSave() {
        if (this.key && this.key.isDirty() && this.key.canSave()) {
            this.key
                .save()
                .then(() => {
                            this.key.reset({member_id: this.props.member.id});
                            this.keyCollection.fetch();
                        });
        }

        const {member} = this.props;
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
        this.unsubscribe.push(member.subscribe(() => this.setState({can_save_member: member.canSave()})));
        this.unsubscribe.push(this.keyCollection.subscribe((keys) => this.setState({keys: keys.items})));
        const key = this.key;
        this.unsubscribe.push(key.subscribe(() => this.setState({can_save_key: key.canSave()})));
        this.unsubscribe.push(this.spanCollection.subscribe(({items}) => {
            this.setState({
                "labaccess_enddate": last_span_enddate(items, "labaccess"),
                "membership_enddate": last_span_enddate(items, "membership"),
                "special_enddate": last_span_enddate(items, "special_labaccess"),
            });
        }));
    }
    
    componentWillUnmount() {
        this.unsubscribe.forEach(u => u());
    }

    render() {
        const {member} = this.props;
        const {can_save_member, can_save_key, keys, has_signed, labaccess_enddate, membership_enddate, special_enddate, pending_labaccess_days} = this.state;

        // Show different content based on if the user has a key or not
        let key_paragraph;
        if (keys.length === 0) {
            key_paragraph = <div className="uk-section">
                    Skapa en ny nyckel genom att läsa in den i fältet nedan och sedan spara.
                    <TextInput model={this.key} tabIndex="1" name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />
                </div>;
        } else if (keys.length === 1) {
            key_paragraph = <p>
                    Användaren har en nyckel registrerad (med id=<span style={{fontFamily: "monospace"}}>{keys[0].tagid}</span>). Kontrollera om hen vet om det och har kvar nyckeln. Gå annars till <a href={"/membership/members/" + member.id + "/keys"}>Nycklar</a> och ta bort den gamla nyckeln, och lägg till en ny.
                </p>;
        } else {
            key_paragraph = <p>
                    Användaren har flera nycklar registrerade! Gå till <a href={"/membership/members/" + member.id + "/keys"}>Nycklar</a> och ta bort alla nycklar utom en.
                </p>;
        }

        // Section 2 and onward shall only be visible after lab contract has been signed
        const section2andon = <>
            <h2>2. Kontrollera legitimation</h2>
            <p>Kontrollera personens legitimation och för in personnummret i fältet nedan. Nyckel kan endast lämnas ut till personen som skall bli medlem.</p>
            <div className="uk-section">
                <TextInput model={member} tabIndex="1" name="civicregno" title="Personnummer" placeholder="YYYYMMDD-XXXX" />
            </div>

            <div className="uk-section">
                <h2>3. Övrig information</h2>
                <p>Kontrollera <b>epost</b> så personen kommer åt kontot, och <b>telefon</b> så vi kan nå hen när det är mer brådskande.</p>
                <div className="uk-grid">
                    <div className="uk-width-1-1"><TextInput model={member} name="email" tabIndex="1" type="email" title="Epost" /></div>
                    <div className="uk-width-1-2"><TextInput model={member} name="phone" tabIndex="1" type="tel" title="Telefonnummer" /></div>
                    <div className="uk-width-1-2"><TextInput model={member} name="address_zipcode" tabIndex="1" type="number" title="Postnummer" /></div>
                </div>
            </div>

            <h2>4. Kontrollera medlemskap </h2>
            <p>Kontrollera om medlemmen har köpt medlemskap och labbmedlemskap.</p>
            <div className="uk-section">
                <DateView title="Föreningsmedlemskap" date={membership_enddate} placeholder="Inget tidigare medlemskap finns registrerat"/>
                <DateView title="Labaccess" date={labaccess_enddate} placeholder="Ingen tidigare labaccess finns registrerad" pending={pending_labaccess_days}/>
                { special_enddate ? 
                    <DateView title="Specialaccess" date={special_enddate}/> : null
                }
            </div>

            <h2>5. Kontrollera nyckel </h2>
            {key_paragraph}

            <div className="uk-section">
                <button className="uk-button uk-button-success uk-float-right" tabIndex="1" disabled={!can_save_member && !can_save_key}><i className="uk-icon-save"/> Spara</button>
            </div>
        </>;

        return (
        <div className="meep">
            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); this.onSave(); return false;}}>
                <h2>1. Ta emot signerat labbmedlemsavtal</h2>
                <p>Kontrollera att labbmedlemsavtalet är signerat och säkerställ att rätt medlemsnummer står väl synligt på labbmedlemsavtalet.</p>
                <div className="uk-section">
                    <input id="signed" className="uk-checkbox" type="checkbox" tabIndex="1" checked={has_signed} onChange={(e) => this.signedChanged(e.target.checked)}/>
                    <label htmlFor="signed"> Signerat labbmedlemsavtal mottaget.</label> 
                </div>

                {has_signed ? section2andon : ""}
            </form>
        </div>
        );
    }
}


export default withRouter(KeyHandoutForm);
