import React from 'react';
import KeyView from './KeyView.jsx';
import auth from '../auth';
import {get} from '../gateway';


const Input = ({value, placeholder, title}) => {
    return (
        <div className="uk-form-row">
            <label className="uk-form-label" htmlFor={name}>{title}</label>
            <div className="uk-form-controls">
                <input placeholder={placeholder} className="uk-input uk-width-1-1"
                       value={value || ""}
                       disabled={true}
                       type="text"/>
            </div>
        </div>
    );
};


export default class Member extends React.Component {
    constructor(props) {
        super(props);
        this.state = {member: {}};
        get({url: "/member/current"}).then(data => this.setState({member: data.data})).catch(() => auth.logout());
    }

    render() {
        const {member: {member_number, firstname, lastname, email, phone, address_street, address_extra, address_zipcode, address_city}} = this.state;
        
        return (
            <div className="meep">
                <h2>Medlem #{member_number}: {firstname} {lastname}</h2>
                <form className="uk-form">
                    <fieldset >
                        <legend><i className="uk-icon-user"/> Personuppgifter</legend>
                        <Input value={firstname} title="Förnamn" />
                        <Input value={lastname}  title="Efternamn" />
                        <Input value={email}     title="E-post" />
                        <Input value={phone}     title="Telefonnummer" />
                    </fieldset>

                    <fieldset data-uk-margin>
                        <legend><i className="uk-icon-home"/> Adress</legend>
                        <Input value={address_street}  title="Address" />
                        <Input value={address_extra}   title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
                        <Input value={address_zipcode} title="Postnummer" />
                        <Input value={address_city}    title="Postort" />
                    </fieldset>

                    <KeyView />

                    <fieldset>
                        <legend><i className="uk-icon-shopping-cart"/> Webshop</legend>
                        <a className="uk-button uk-button-default uk-margin-top" href="/shop/member/history">Visa köphistorik</a>
                        <a className="uk-button uk-button-default uk-margin-top uk-margin-left" href="/shop/">Gå till webshoppen</a>
                    </fieldset>

                    <div className="uk-form-row">
                        <button type="button" onClick={this.props.logout} className="uk-button uk-button-secondary uk-float-right uk-margin-right"><span className="uk-icon-sign-out" /> Logga ut</button>
                    </div>
                </form>
            </div>
        );
    }
}

