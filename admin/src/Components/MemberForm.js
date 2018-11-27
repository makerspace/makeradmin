import React from 'react';
import CountryDropdown from './CountryDropdown';
import DateTimeShow from "./DateTimeShow";
import TextInput from "./TextInput";
import {withRouter} from "react-router";


class MemberForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {member} = this.props;
        this.unsubscribe = member.subscribe(() => this.setState({saveDisabled: !member.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const {member, onSave, onDelete} = this.props;
        const {saveDisabled} = this.state;
        
        return (
            <div className="meep">
                <form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                    <fieldset >
                        <legend><i className="uk-icon-user"/> Personuppgifter</legend>

                        <TextInput model={member} name="civicregno" title="Personnummer" />
                        <TextInput model={member} name="firstname" title="Förnamn" />
                        <TextInput model={member} name="lastname" title="Efternamn" />
                        <TextInput model={member} name="email" title="E-post" />
                        <TextInput model={member} name="phone" title="Telefonnummer" />
                    </fieldset>

                    <fieldset data-uk-margin>
                        <legend><i className="uk-icon-home"/> Adress</legend>

                        <TextInput model={member} name="address_street" title="Address" />
                        <TextInput model={member} name="address_extra" title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
                        <TextInput model={member} name="address_zipcode" title="Postnummer" />
                        <TextInput model={member} name="address_city" title="Postort" />

                        <div className="uk-form-row">
                            <label htmlFor="" className="uk-form-label">Land</label>
                            <div className="uk-form-controls">
                                <CountryDropdown model={member} name="address_country"/>
                            </div>
                        </div>
                    </fieldset>
     
                    {member.id
                     ?
                     <fieldset data-uk-margin>
                         <legend><i className="uk-icon-tag"/> Metadata</legend>
                         
                         <div className="uk-form-row">
                             <label className="uk-form-label">Medlem sedan</label>
                             <div className="uk-form-controls">
                                 <i className="uk-icon-calendar"/>
                                 &nbsp;
                                 <DateTimeShow date={member.created_at} />
                             </div>
                         </div>
                         
                         <div className="uk-form-row">
                             <label className="uk-form-label">Senast uppdaterad</label>
                             <div className="uk-form-controls">
                                 <i className="uk-icon-calendar"/>
                                 &nbsp;
                                 <DateTimeShow date={member.updated_at} />
                             </div>
                         </div>
                     </fieldset>
                     :
                     ""}

                    <div className="uk-form-row">
                        {member.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Ta bort medlem</a> : ""}
                        <button className="uk-button uk-button-success uk-float-right" disabled={saveDisabled}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
                    </div>
                </form>
            </div>
        );
    }
}


export default withRouter(MemberForm);
