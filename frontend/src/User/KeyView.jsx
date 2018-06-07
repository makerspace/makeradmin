import React from 'react';
import { withRouter } from 'react-router'

// import CountryDropdown from '../../../CountryDropdown'
import DateTimeField from '../Components/DateTime'
import MemberModel from './Models/Member'
import Input from '../Components/Form/Input.jsx'
import GenericEntityFunctions from '../GenericEntityFunctions'
import auth from '../auth'

module.exports = withRouter(class Member extends React.Component
{
	constructor(props)
	{
		super(props);

		this.state = {
			keys: null,
		};

		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/member/current/keys",
			cache: false,
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			}
		}).done((data, textStatus, xhr) => {
			console.log(data);
			this.setState({
				keys: data.data
			});
		}).fail((xhr, textStatus, error) => {
			UIkit.modal.alert("<h2>Misslyckades med att hämta nycklar</h2>Tog emot ett oväntat svar från servern:<br><br>" + xhr.status + " " + xhr.statusText + "<br><br>" + xhr.responseText);
		});
	}

	renderKeys(keys)
	{
		if (keys == null) {
			return (
				<p>Laddar...</p>
			);
		} else {
			let prefix = keys.length > 1 ? "Nyckeln" : "Din nyckel";
			let arr = keys.map(key => {
				let text = "";
				let icon = "";
				let color = "";
				let sortKey = 0;
				const id = key.key_id;

				if (key.startdate != null && key.enddate != null && key.status == "active") {
					const start = Date.parse(key.startdate);
					const end = Date.parse(key.enddate);

					const millisecondsPerHour = 1000 * 3600;
					const millisecondsPerDay = millisecondsPerHour * 24;
					sortKey = end - Date.now();

					if (Date.now() >= start) {
						const remainingDays = Math.floor((end - Date.now()) / millisecondsPerDay);

						if (remainingDays < -1) {
							text = prefix + " är ogiltig sedan " + (-remainingDays) + " dagar.";
							icon = "uk-icon-times";
							color = "member-key-color-inactive";
						} else if (remainingDays < 0) {
							text = prefix + " gick ut idag.";
							icon = "uk-icon-times";
							color = "member-key-color-inactive";
						} else if (remainingDays < 1) {
							const remainingHours = Math.ceil((end - Date.now()) / millisecondsPerHour);
							text = prefix + " är giltig i mindre än " + remainingHours + " timmar till.";
							icon = "uk-icon-check";
							color = "member-key-color-warning";
						} else if (remainingDays < 14) {
							text = prefix + " är endast giltig i " + remainingDays + " dagar till. Kom ihåg att förnya den innan nästa nyckelutlämning.";
							icon = "uk-icon-check";
							color = "member-key-color-warning";
						} else {
							text = prefix + " är giltig i " + remainingDays + " dagar till.";
							icon = "uk-icon-check";
							color = "member-key-color-active";
						}
					} else {
						sortKey = 0;
						const remainingDays = Math.floor((end - Date.now()) / millisecondsPerDay);
						text = prefix + " blir aktiv " + start.toLocaleDateString("sv-se");
						icon = "uk-icon-times";
						color = "member-key-color-inactive";
					}
				} else {
					sortKey = -1e28;
					text = prefix + " är inaktiv.";
					icon = "uk-icon-times";
					color = "member-key-color-inactive";
				}

				return {
					key, text, icon, color, sortKey, id
				}
			});
			arr.sort((a,b) => b.sortKey - a.sortKey);
			return arr.map(o => (
				<div key={o.id} className="member-key-box"><div className={"uk-icon-small member-key-icon " + o.icon + " " + o.color}></div><div className="member-key-tag">{o.key.tagid}</div><div className="member-key-status">{o.text}</div></div>
			));
		}
	}

	render()
	{
		console.log("Rendering: ");
		console.log(this.state.keys);
		return (
			<fieldset data-uk-margin>
				<legend><i className="uk-icon-key"></i> Nycklar</legend>
				{this.renderKeys(this.state.keys)}
			</fieldset>
		);
	}
});
