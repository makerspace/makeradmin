import React from 'react';
import CountryDropdown from '../../CountryDropdown';
import DateTime from "../../Components/Form/DateTime";
import Input2 from "../../Components/Form/Input2";


// TODO Maybe not really a reusable component, check usages later.
export default class MemberForm extends React.Component {

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
        const {member, onSave, onRemove} = this.props;
        const {saveDisabled} = this.state;
        
		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"/> Personuppgifter</legend>

						<Input2 model={member} name="civicregno" title="Personnummer" />
						<Input2 model={member} name="firstname" title="Förnamn" />
						<Input2 model={member} name="lastname" title="Efternamn" />
						<Input2 model={member} name="email" title="E-post" />
						<Input2 model={member} name="phone" title="Telefonnummer" />
					</fieldset>

					<fieldset data-uk-margin>
						<legend><i className="uk-icon-home"/> Adress</legend>

						<Input2 model={member} name="address_street" title="Address" />
						<Input2 model={member} name="address_extra" title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
						<Input2 model={member} name="address_zipcode" title="Postnummer" />
						<Input2 model={member} name="address_city" title="Postort" />

						<div className="uk-form-row">
							<label htmlFor="" className="uk-form-label">Land</label>
							<div className="uk-form-controls">
								<CountryDropdown country={member.address_country} onChange={c => member.address_country = c} />
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
                                 <DateTime date={member.created_at} />
                             </div>
                         </div>
                         
                         <div className="uk-form-row">
                             <label className="uk-form-label">Senast uppdaterad</label>
                             <div className="uk-form-controls">
                                 <i className="uk-icon-calendar"/>
                                 &nbsp;
                                 <DateTime date={member.updated_at} />
                             </div>
                         </div>
                     </fieldset>
                     :
                     ""}

					<div className="uk-form-row">
                        {member.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onRemove}><i className="uk-icon-trash"/> Ta bort medlem</a> : ""}
                        <button type="button" className="uk-button uk-button-success uk-float-right" disabled={saveDisabled} onClick={onSave}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
					</div>
				</form>
			</div>
		);
	}
}
