import React from 'react'

var StatisticsHandler = React.createClass({
	render: function () {
		return (
			<div className="uk-width-1-1">
				<h2>Statistik</h2>
				<p>Här är det tänkt att visas diverse statistik. Förslagsvis bygger vi en enkel, men kraftfull, statistikmotor i tre lager. Självklart med möjlighet att exportera *.csv och *.svg</p>
				<p></p>
				<ul>
					<li>1. Datakälla - Levererar den data som används för att generera statistik. Bör fungera med det befintliga API:t</li>
					<li>
						2. Filter - Filtrerar / strukturerar / grupperar data på olika sätt
						<ul>
							<li>Filter - filtrera på datumintervall etc</li>
							<li>Gruppering - Beräkna min/max/avg för dagar, veckor, månader, etc</li>
						</ul>
					</li>
					<li>3. Generering av grafer - genererar interaktiva grafer med hjälp av lämpligt HTML5 / Javascript-bibliotek.</li>
				</ul>
			</div>
		);
	}
});

module.exports = StatisticsHandler