import React from 'react'
import { Link } from 'react-router'
//import OverviewTable from '../Components/Tables/Overview'

// Backbone
//import OverviewCollection from '../Collections/Overview'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h1>Rutiner för nyckelutlämnning</h1>

				<h2>1) Förberedelser i god tid nyckelutlämning</h2>
				<div className="uk-margin-large-left">
					<ul>
						<li>Boka nyckeldator</li>
						<li>Annonsera ut i kalendarium</li>
					</ul>
				</div>

				<h2>2) Förberedelser strax innan nyckelutlämning</h2>
				<div className="uk-margin-large-left">
					<p>OBS: Christian ansvarar för att detta blir gjort innan. Detta är procedurer som på sikt skall automatiseras bort till 100%.</p>

					<h3>2a) Kontrollera att alla Tictail-ordrar är synkade</h3>
					<p>Ordrar hämtas automatiskt hem från Tictail en gång i timmen. Det ken däremot vara bra kolla igenom så att allting verkligen är synkroniserat. Gå till <Link to="/auto/tictail">Tictail-ordrar</Link> och kolla så att det finns ett värde i kolumnen "Local storage" på de senaste ordrarna. Om det inte gör det, klicka på knappen "Ladda hem ordrar från Tictail" för att exekvera en manuell synkronisering. Om något gör en beställning under en nyckelutlämning måste denna manuella nedladdning göras.</p>

					<h3>2b) Skapa verifikationer</h3>
					<p>När all Tictail-data finns i systemet är nästa steg att skapa bokföringsposter. Detta gör man genom att TODO...</p>

					<h3>2c) Skapa nya medlemmar</h3>
					<p>TODO</p>

					<h3>2d) Gör manuella kopplingar mellan ordrar och medlemmar</h3>
					<p>TODO</p>

					<h3>2e) TODO: Förläng befintliga medlemskap</h3>
					<p>TODO</p>
				</div>

				<h2>3) Rutiner under nyckelutlämning</h2>
				<div className="uk-margin-large-left">
					<h3>3a) TODO: Förläng labbaccess</h3>
					<p>TODO</p>

					<h3>3b) Synkronisera passersystem</h3>
					<p>TODO</p>
				</div>

				<h2>3) Rutiner vid utlämning av nya nycklar</h2>
				<div className="uk-margin-large-left">
					<ul>
						<li>Låt personen skriva på lokalavtal och kontrollera identitet</li>
						<li>Lägg in en nyckel i MakerAdmin på medlemmen och sätt korrekt slutdatum</li>
						<li>Skicka ett mail med slutdatum för labbaccess</li>
						<li>Replikera över ovanstående data till MultiAccess</li>
					</ul>
				</div>
			</div>
		);
	},
});