import React from 'react'
import { Link } from 'react-router'
import DateField from '../../Components/Date'
import auth from '../../auth'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			data: null,
			fetched_data: false,
		};
	},

	componentWillReceiveProps: function(props)
	{
		if(props.filename !== "")
		{
			$.ajax({
				url: config.apiBasePath + "/multiaccess/file/" + props.filename,
				dataType: "json",
				cache: false,
				headers: {
					"Authorization": "Bearer " + auth.getAccessToken()
				},
				success: function(data)
				{
					this.setState({data: data});
					this.setState({fetched_data: true});
				}.bind(this),
				error: function(xhr, status, err)
				{
					console.error(this.props.url, status, err.toString());
				}.bind(this)
			});
		}
	},

	render: function()
	{
		if(this.state.fetched_data == false)
		{
			return (<p>Loading data</p>);
		}
		else
		{
			var members = [];
			this.state.data.data.map(function (row, i) {
				var errors = [];

				if(row.multiaccess_key.length != 0 && row.local_key.length != 0)
				{
					// Compare start date
					if(row.multiaccess_key.startdate != row.local_key.startdate)
					{
						errors.push(
							<div>
								<h4>Startdatumet är fel</h4>
								<p>MultiAccess: <DateField date={row.multiaccess_key.startdate} /></p>
								<p>MakerAdmin: <DateField date={row.local_key.startdate} /></p>
							</div>
						);
					}

					// Compare end date
					if(row.multiaccess_key.enddate != row.local_key.enddate)
					{
						errors.push(
							<div>
								<h4>Slutdatumet är fel</h4>
								<p>MultiAccess: <DateField date={row.multiaccess_key.enddate} /></p>
								<p>MakerAdmin: <DateField date={row.local_key.enddate} /></p>
							</div>
						);
					}

					// Compare tagid
					if(row.multiaccess_key.tagid != row.local_key.tagid)
					{
						errors.push(
							<div>
								<h4>RFID-taggen överensstämmer ej</h4>
								<p>MultiAccess: {row.multiaccess_key.tagid}</p>
								<p>MakerAdmin: {row.local_key.tagid}</p>
							</div>
						);
					}

					// Compare active
					if(row.multiaccess_key.active == false && row.local_key.status != "inactive")
					{
						errors.push(
							<div>
								<h4>Nyckeln skall inaktiveras i MultiAccess</h4>
							</div>
						);
					}
					if(row.multiaccess_key.active == true && row.local_key.status != "active")
					{
						errors.push(
							<div>
								<h4>Nyckeln skall aktiveras i MultiAccess</h4>
							</div>
						);
					}
				}

				if(row.multiaccess_key.length == 0)
				{
					errors.push(
						<div>
							<h4>Nyckeln saknas i MultiAccess</h4>
							<p>RFID: {row.local_key.tagid}</p>

							{row.local_key.title ?
								<p>Titel: {row.local_key.title}</p>
							:""}

							{row.local_key.description ?
								<p>Beskrivning: {row.local_key.description}</p>
							:""}
						</div>
					);
				}

				if(row.local_key.length == 0)
				{
					errors.push(
						<div>
							<h4>Nyckeln saknas i MakerAdmin</h4>
						</div>
					);
				}

				if(row.member.length == 0)
				{
					errors.push(
						<div>
							<h4>Personen saknas i medlemsregistret</h4>
						</div>
					);
				}

				row.errors.map(function (error, i) {
					errors.push(
						<div>
							<h4>{error}</h4>
						</div>
					);
				});

				members.push({
					"member": row.member,
					"local_key": row.local_key,
					"multiaccess_key": row.multiaccess_key,
					"errors": errors,
				});
			});

			return (
				<div className="multiaccess">
					{members.map(function (row, i) {
						if(row.errors.length > 0)
						{
							return [
								<div className="uk-placeholder">
									<h3></h3>

									{row.member.length != 0 ?
										<p><i className="uk-icon-user" /> Medlem: <Link to={"/membership/members/" + row.member.member_id}>{row.member.member_number} {row.member.firstname} {row.member.lastname}</Link></p>
									:""}

									{row.local_key.length != 0 ?
										<p><i className="uk-icon-key" /> MakerAdmin: <Link to={"/keys/" + row.local_key.key_id}>{row.local_key.tagid} {row.local_key.title}</Link></p>
									:""}

									{row.multiaccess_key.length != 0 ?
										<p><i className="uk-icon-key" /> MultiAccess: {row.multiaccess_key.tagid} {row.multiaccess_key.member_number}</p>
									:""}

										{
											row.errors.map(function (error, i) {return [
												<div className="error">
													{error}
												</div>
											];})
										}
								</div>
							];
						}
					})}
				</div>
			);
		}
	}
});