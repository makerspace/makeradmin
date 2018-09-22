import React from 'react';
import { withRouter } from 'react-router'

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

	renderInfo(info, templateStrings)
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
					text = templateStrings[0](-remainingDays);
					icon = "uk-icon-times";
					color = "member-key-color-inactive";
				} else if (remainingDays < 0) {
					text = templateStrings[1]();
					icon = "uk-icon-times";
					color = "member-key-color-inactive";
				} else if (remainingDays < 1) {
					const remainingHours = Math.ceil((end - Date.now()) / millisecondsPerHour);
					text = templateStrings[2](remainingHours);
					icon = "uk-icon-check";
					color = "member-key-color-warning";
				} else if (remainingDays < 14) {
					text = templateStrings[3](remainingDays);
					icon = "uk-icon-check";
					color = "member-key-color-warning";
				} else {
					text = templateStrings[4](remainingDays);
					icon = "uk-icon-check";
					color = "member-key-color-active";
				}
			} else {
				text = templateStrings[5]();
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
		let labaccessStrings = [
			(days) => `Din labaccess är ogiltig sedan ${days} dagar.`,
			() => `Din labaccess gick ut idag.`,
			(hours) => `Din labaccess är giltig i mindre än ${hours} timmar till.`,
			(days) => `Din labaccess är endast giltig i ${days} dagar till. Kom ihåg att förnya den innan nästa nyckelutlämning.`,
			(days) => `Din labaccess är giltig i ${days} dagar till.`,
			() => `Din labaccess är inaktiv.`,
		];

		let membershipStrings = [
			(days) => `Ditt föreningsmedlemsskap är ogiltigt sedan ${days} dagar.`,
			() => `Ditt föreningsmedlemsskap gick ut idag.`,
			(hours) => `Ditt föreningsmedlemsskap är giltigt i mindre än ${hours} timmar till.`,
			(days) => `Ditt föreningsmedlemsskap är endast giltigt i ${days} dagar till.`,
			(days) => `Ditt föreningsmedlemsskap är giltigt i ${days} dagar till.`,
			() => `Ditt föreningsmedlemsskap är inaktivt.`,
		];

		let calendarURL = "https://www.makerspace.se/kalendarium";
		let pendingAccess = "";
		if (this.state.pendingLabaccessDays > 0) {
			pendingAccess = <p>Du har {this.state.pendingLabaccessDays} dagar som kommer att läggas till på din labaccess vid nästa <a href={calendarURL}>nyckelutlämning</a>.</p>;
		} else {
			pendingAccess = <p>Om du köper ny labaccess i webshoppen så kommer den aktiveras vid nästa <a href={calendarURL}>nyckelutlämning</a>.</p>;
		}

		return (
			<fieldset data-uk-margin>
				<legend><i className="uk-icon-key"></i> Medlemsskap</legend>
				{this.renderInfo(this.state.info_membership, membershipStrings)}
				{this.renderInfo(this.state.info_labaccess, labaccessStrings)}
				{pendingAccess}
			</fieldset>
		);
	}
});
