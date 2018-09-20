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
			pendingLabaccessDays: 0,
		};

		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/member/current/membership",
			cache: false,
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			}
		}).done((data, textStatus, xhr) => {
			this.setState({
				info_labaccess: {
					active: data.data.has_labaccess,
					enddate: data.data.labaccess_end,
				},
				info_membership: {
					active: data.data.has_membership,
					enddate: data.data.membership_end,
				}
			});
		}).fail((xhr, textStatus, error) => {
			if (xhr.status != 401) {
				UIkit.modal.alert("<h2>Misslyckades med att hämta nycklar</h2>Tog emot ett oväntat svar från servern:<br><br>" + xhr.status + " " + xhr.statusText + "<br><br>" + xhr.responseText);
			}
		});

		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/webshop/member/current/pending_actions",
			cache: false,
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			}
		}).done((data, textStatus, xhr) => {
			let pendingLabaccessDays = 0;
			let actions = data.data;
			for (let pending of actions) {
				if (pending.action.name == "add_labaccess_days") {
					pendingLabaccessDays += pending.pending_action.value;
				}
			}
			this.setState({pendingLabaccessDays: pendingLabaccessDays});
		});
	}

	renderInfo(info, prefix)
	{
		if (info == null) {
			return (
				<p>Laddar...</p>
			);
		} else {
			let text = "";
			let icon = "";
			let color = "";

			const end = Date.parse(info.enddate);

			const millisecondsPerHour = 1000 * 3600;
			const millisecondsPerDay = millisecondsPerHour * 24;

			if (info.active) {
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
				text = prefix + " är inaktiv.";
				icon = "uk-icon-times";
				color = "member-key-color-inactive";
			}

			return (
				<div className="member-key-box"><div className={"uk-icon-small member-key-icon " + icon + " " + color}></div><div className="member-key-status">{text}</div></div>
			);
		}
	}

	render()
	{
		let pendingAccess = "";
		if (this.state.pendingLabaccessDays > 0) {
			pendingAccess = <p>Du har {this.state.pendingLabaccessDays} dagar som kommer att läggas till på din labaccess vid nästa nyckelutlämning.</p>;
		} else {
			pendingAccess = <p>Om du köper ny labaccess i webshoppen så kommer den aktiveras vid nästa nyckelutlämning.</p>;
		}

		return (
			<fieldset data-uk-margin>
				<legend><i className="uk-icon-key"></i> Medlemsskap</legend>
				{this.renderInfo(this.state.info_labaccess, "Din labaccess")}
				{pendingAccess}
				
			</fieldset>
		);

		// Disabled until membership is actually supported
		// {this.renderInfo(this.state.info_membership, "Ditt medlemsskap")}
	}
});
