import React from 'react';
// TODO Replace global input if it works.
// import Input from '../../Components/Form/Input';
import classNames from 'classnames/bind';
import CountryDropdown from '../../CountryDropdown';
import DateTime from "../../Components/Form/DateTime";


class Input extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            value: '',
            selected: false,
            isDirty: false,
        };
    }

    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(() => this.setState({value: model[name] === null ? '' : model[name], isDirty: model.isDirty(name)}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {value, selected, isDirty} = this.state;
        const {model, name, title, icon, disabled, placeholder, formrow} = this.props;
        
        const classes = classNames(name,
                                   {
                                       "uk-form-row": formrow,
                                       "selected": selected,
                                       "changed": isDirty,
                                   });
        
        const input = <input id={name} name={name} type="text" placeholder={placeholder || title} className="uk-form-width-large"
                             value={value} disabled={disabled}
                             onChange={(event) => model[name] = event.target.value}
                             onFocus={() => this.setState({selected: true})}
                             onBlur={() => this.setState({selected: false})}/>;
        
        return (
            <div className={classes}>
                <label htmlFor={name} className="uk-form-label">{title}</label>
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{input}</div> : input}
                </div>
            </div>
        );
    }
}

Input.defaultProps = {
    formrow: true,
};

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
        const {member, onCancel, onSave, onRemove} = this.props;
        const {saveDisabled} = this.state;
        
		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"/> Personuppgifter</legend>

						<Input model={member} name="civicregno" title="Personnummer" />
						<Input model={member} name="firstname" title="Förnamn" />
						<Input model={member} name="lastname" title="Efternamn" />
						<Input model={member} name="email" title="E-post" />
						<Input model={member} name="phone" title="Telefonnummer" />
					</fieldset>

					<fieldset data-uk-margin>
						<legend><i className="uk-icon-home"/> Adress</legend>

						<Input model={member} name="address_street" title="Address" />
						<Input model={member} name="address_extra" title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
						<Input model={member} name="address_zipcode" title="Postnummer" />
						<Input model={member} name="address_city" title="Postort" />

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
                        <a className="uk-button uk-button-danger uk-float-left" onClick={onCancel}><i className="uk-icon-close"/> Avbryt</a>
                        {member.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onRemove}><i className="uk-icon-trash"/> Ta bort medlem</a> : ""}
                        <button type="button" className="uk-button uk-button-success uk-float-right" disabled={saveDisabled} onClick={onSave}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
					</div>
				</form>
			</div>
		);
	}
}
