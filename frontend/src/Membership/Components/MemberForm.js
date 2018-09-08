import React from 'react';
// import Input from '../../Components/Form/Input';
import classNames from 'classnames/bind';


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
        this.unsubscribe = model.subscribe(() => this.setState({value: model[name], isDirty: model.isDirty(name)}));
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

const CountryDropdown = () => <div/>;
const DateTimeField = () => <div/>;

// TODO Maybe not really a reusable component, check usages later.
export default class MemberAdd extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {model} = this.props;
        this.unsubscribe = model.subscribe(() => this.setState({saveDisabled: !model.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    remove() {
        console.info("remove");
        // TODO Implement remove.
    }
    
    render() {
        const {model, onCancel, onSave} = this.props;
        const {saveDisabled} = this.state;
        
		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"/> Personuppgifter</legend>

						<Input model={model} name="civicregno" title="Personnummer" />
						<Input model={model} name="firstname"  title="Förnamn" />
						<Input model={model} name="lastname"   title="Efternamn" />
						<Input model={model} name="email"      title="E-post" />
						<Input model={model} name="phone"      title="Telefonnummer" />
					</fieldset>

					<fieldset data-uk-margin>
						<legend><i className="uk-icon-home"/> Adress</legend>

						<Input model={model} name="address_street"  title="Address" />
						<Input model={model} name="address_extra"   title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
						<Input model={model} name="address_zipcode" title="Postnummer" />
						<Input model={model} name="address_city"    title="Postort" />

						<div className="uk-form-row">
							<label htmlFor="" className="uk-form-label">Land</label>
							<div className="uk-form-controls">
								<CountryDropdown country={model.address_country} onChange={this.changeCountry} />
							</div>
						</div>
					</fieldset>
     
					{model.id
                     ?
                     <fieldset data-uk-margin>
                         <legend><i className="uk-icon-tag"/> Metadata</legend>
                         
                         <div className="uk-form-row">
                             <label className="uk-form-label">Medlem sedan</label>
                             <div className="uk-form-controls">
                                 <i className="uk-icon-calendar"/>
                                 &nbsp;
                                 <DateTimeField date={model.created_at} />
                             </div>
                         </div>
                         
                         <div className="uk-form-row">
                             <label className="uk-form-label">Senast uppdaterad</label>
                             <div className="uk-form-controls">
                                 <i className="uk-icon-calendar"/>
                                 &nbsp;
                                 <DateTimeField date={model.updated_at} />
                             </div>
                         </div>
                     </fieldset>
                     :
                     ""}

					<div className="uk-form-row">
                        <a className="uk-button uk-button-danger uk-float-left" onClick={onCancel}><i className="uk-icon-close"/> Avbryt</a>
                        {model.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={null}><i className="uk-icon-trash"/> Ta bort medlem</a> : ""}
                        <button type="button" className="uk-button uk-button-success uk-float-right" disabled={saveDisabled} onClick={onSave}><i className="uk-icon-save"/> {model.id ? 'Spara' : 'Skapa'}</button>
					</div>
				</form>
			</div>
		);
	}
}

/*

import BackboneReact from 'backbone-react-component';
import {Link, withRouter} from 'react-router';

import CountryDropdown from '../../../CountryDropdown'
import DateTimeField from '../../../Components/DateTime'

import GenericEntityFunctions from '../../../GenericEntityFunctions'

import Input from '../../../Components/Form/Input';



module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	componentWillMount: function(){
		// The groups attribute should not affect the isDirty() function on the model
		this.getModel().ignoreAttributes.push("groups");
	},

	removeTextMessage: function(member)
	{
		return "Är du säker på att du vill ta bort medlemmen \"#" + member.member_number + " " + member.firstname + " " + member.lastname + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/membership/members");
	},

	onRemoveError: function()
	{
		UIkit.notify("Ett fel uppstod vid borttagning av medlem", {timeout: 0, status: "danger"});
	},

	onCreate: function(model)
	{
		UIkit.notify("Successfully created", {status: "success"});
		this.props.router.push("/membership/members/" + model.get("member_id"));
	},

	onUpdate: function(model)
	{
		UIkit.notify("Successfully updated", {status: "success"});
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving member", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/membership/members");
	},

	changeCountry: function(country)
	{
		this.getModel().set({
			address_country: country
		});
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate required fields
		if(
			this.getModel().isDirty() &&
			this.state.model.firstname.length > 0 &&
			this.state.model.email.length > 0
		)
		{
			// Enable button
			return true;
		}

		// Disable button
		return false;
	},

	render: function()
	{
		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"></i> Personuppgifter</legend>

						<Input model={this.getModel()} name="civicregno" title="Personnummer" />
						<Input model={this.getModel()} name="firstname"  title="Förnamn" />
						<Input model={this.getModel()} name="lastname"   title="Efternamn" />
						<Input model={this.getModel()} name="email"      title="E-post" />
						<Input model={this.getModel()} name="phone"      title="Telefonnummer" />
					</fieldset>

					<fieldset data-uk-margin>
						<legend><i className="uk-icon-home"></i> Adress</legend>

						<Input model={this.getModel()} name="address_street"  title="Address" />
						<Input model={this.getModel()} name="address_extra"   title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
						<Input model={this.getModel()} name="address_zipcode" title="Postnummer" />
						<Input model={this.getModel()} name="address_city"    title="Postort" />

						<div className="uk-form-row">
							<label htmlFor="" className="uk-form-label">Land</label>
							<div className="uk-form-controls">
								<CountryDropdown country={this.state.model.address_country} onChange={this.changeCountry} />
							</div>
						</div>
					</fieldset>

					{this.state.model.member_id > 0 ?
						<fieldset data-uk-margin>
							<legend><i className="uk-icon-tag"></i> Metadata</legend>

							<div className="uk-form-row">
								<label className="uk-form-label">Medlem sedan</label>
								<div className="uk-form-controls">
									<i className="uk-icon-calendar"></i>
									&nbsp;
									<DateTimeField date={this.state.model.created_at} />
								</div>
							</div>

							<div className="uk-form-row">
								<label className="uk-form-label">Senast uppdaterad</label>
								<div className="uk-form-controls">
									<i className="uk-icon-calendar"></i>
									&nbsp;
									<DateTimeField date={this.state.model.updated_at} />
								</div>
							</div>
						</fieldset>
					: ""}

					<div className="uk-form-row">
						{this.cancelButton()}
						{this.removeButton("Ta bort medlem")}
						{this.saveButton("Spara personuppgifter")}
					</div>
				</form>
			</div>
		);
	},
}));
*/