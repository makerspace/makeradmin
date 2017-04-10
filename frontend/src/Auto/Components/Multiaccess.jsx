import React from 'react'
import { Link } from 'react-router'
import DateField from '../../Components/DateTime'
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
		var date_mismatch = [];
		var members = [];

		if(this.state.fetched_data == false)
		{
			return (<p>Loading data</p>);
		}
		else
		{
			this.state.data.data.map(function (row, i) {
				var errors = [];

				if(row.multiaccess_key.length != 0 && row.local_key.length != 0)
				{
					// Compare start date
					// Compare end date (Less than 8 hours)
					// Compare active
					if(
						(row.multiaccess_key.startdate != row.local_key.startdate) ||
						(Math.abs(new Date(row.multiaccess_key.enddate) - new Date(row.local_key.enddate)) > (36 * 3600 * 1000)) ||
						(row.multiaccess_key.active == false && row.local_key.status != "inactive") ||
						(row.multiaccess_key.active == true && row.local_key.status != "active")
					)
					{
						date_mismatch.push({
							"multiaccess_key": row.multiaccess_key,
							"member": row.member,
							"local_key": row.local_key,
						});
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
					<h3>Felaktiga datum</h3>
					<table>
						<thead>
							<tr>
								<th>Medlem</th>
								<th>MakerAdmin</th>
								<th>MultiAccess</th>
								<th>Meep</th>
							</tr>
						</thead>
						<tbody>
							{date_mismatch.map(function (row, i) {
								return (
									<tr key={i}>
										<td><i className="uk-icon-user" /> <Link to={"/membership/members/" + row.member.member_id}>{row.member.member_number} {row.member.firstname} {row.member.lastname}</Link></td>
										<td>
											{row.local_key.status != "active" ?
													<em>Inaktiv</em>
												:
													<DateField date={row.local_key.enddate} />
											}
										</td>
										<td>
											{row.multiaccess_key.active == false ? 
													<em>Inaktiv</em>
												:
													<DateField date={row.multiaccess_key.enddate} />
											}
										</td>
										<td></td>
									</tr>
								);
							})}
						</tbody>
					</table>

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