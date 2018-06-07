import React from 'react';
import { withRouter } from 'react-router'

// import CountryDropdown from '../../../CountryDropdown'
import DateTimeField from '../Components/DateTime'
import MemberModel from './Models/Member'
import Input from '../Components/Form/Input.jsx'
import GenericEntityFunctions from '../GenericEntityFunctions'
import KeyView from './KeyView.jsx'

module.exports = withRouter(class Member extends React.Component
{
	constructor(props)
	{
		super(props);
		var member = new MemberModel({
		});

		member.fetch({success: () => {
			// Since we do not use BackboneReact we have to update the view manually
			this.forceUpdate();
			console.log("Updated" + member.email + " " + member.created_at);
		}});

		member.on("change sync", () => {
			this.forceUpdate();
		});

		this.state = {
			model: member,
		};
	}

	getModel()
	{
		return this.state.model;
	}

	changeCountry()
	{
		this.getModel().set({
			address_country: country
		});
	}

	saveEntity(event)
	{
		console.log(this.getModel().created_at);
		GenericEntityFunctions.saveEntity.bind(this)(event);
	}

	render()
	{
		return (
			<div className="meep">
				<h2>Medlem #{this.state.model.get("member_number")}: {this.state.model.get("firstname")} {this.state.model.get("lastname")}</h2>
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"></i> Personuppgifter</legend>

						{/*<Input model={this.getModel()} name="civicregno" title="Personnummer" />*/}
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

						{/*<div className="uk-form-row">
							<label htmlFor="" className="uk-form-label">Land</label>
							<div className="uk-form-controls">
								<CountryDropdown country={this.state.model.address_country} onChange={this.changeCountry} />
							</div>
						</div>*/}
					</fieldset>

					<fieldset data-uk-margin>
						<div className="uk-form-row">
							<label className="uk-form-label">Medlem sedan {this.state.model.created_at}.</label>
							<div className="uk-form-controls">
								<i className="uk-icon-calendar"></i>
								&nbsp;
								<DateTimeField date={this.state.model.created_at} />
							</div>
						</div>
					</fieldset>
					<KeyView />

					<fieldset >
						<legend><i className="uk-icon-shopping-cart"></i> Köphistorik</legend>
						<a className="uk-button uk-button-default uk-margin-top" href={"/shop/member/" + this.state.model.get('member_id') + "/history"}>Visa köphistorik</a>
					</fieldset>

					<div className="uk-form-row">
						{/*<button className="uk-button uk-button-success uk-float-right uk-margin-right" onClick={this.saveEntity.bind(this)}><i className="uk-icon-save"></i> Spara</button>*/}
						<button type="button" onClick={this.props.logout} className="uk-button uk-button-secondary uk-float-right uk-margin-right"><span className="uk-icon-sign-out" /> Logga ut</button>
					</div>
				</form>
			</div>
		);
	}
});
