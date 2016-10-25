import React from 'react'

var SettingsAutomationHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Automation</h2>
				<p>Här skall man kunna konfiguera diverse automation. Systemet bygger på att när ett event sker får man möjlighet att fånga upp detta för att sedan trigga ett nytt event.</p>
				<ul>
					<li>
						När en ny medlem registrerar sig
						<ul><li>Skicka ett mail enligt mall</li></ul>
					</li>

					<li>
						När en produkt av typen labbavgift är betald
						<ul>
							<li>Skicka ett kvitto via mail enligt mall</li>
							<li>Lägg till en ny period för labbavgift i databasen</li>
						</ul>
					</li>

					<li>
						När ett medlemskap löper ut om 30 dagar
						<ul><li>Skicka ett mail enligt mall</li></ul>
					</li>

					<li>
						När ett medlemskap löper ut om 7 dagar
						<ul><li>Skicka ett mail enligt mall</li></ul>
					</li>

					<li>
						När ett medlemskap löpt ut
						<ul><li>Skicka ett mail enligt mall</li></ul>
					</li>

					<li>
						Etc...
					</li>
				</ul>
			</div>
		);
	},
});

module.exports = SettingsAutomationHandler