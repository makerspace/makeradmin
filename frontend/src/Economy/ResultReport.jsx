import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import MasterledgerCollection from '../Backbone/Collections/Masterledger'

import { Link } from 'react-router'
import Currency from '../Formatters/Currency'
import DateField from '../Formatters/Date'
import BackboneTable from '../BackboneTable'

var EconomyResultReportHandler = React.createClass({
	getInitialState: function()
	{
		return {
			data: [],
			fetched_data: false
		};
	},

	componentDidMount: function()
	{
		$.ajax({
			url: "/api/v2/economy/2015/resultreport",
			dataType: 'json',
			cache: false,
			success: function(data) {
				this.setState({data: data});
				this.setState({fetched_data: true});
			}.bind(this),
			error: function(xhr, status, err) {
				console.error(this.props.url, status, err.toString());
			}.bind(this)
		});
	},

	renderRecursive: function (data, depth = 1)
	{
		var _this = this;
		return data.map(
			function (row, i)
			{
				return (
					[
						<tr>
							<td colSpan={depth}>
								&nbsp;
							</td>
							<td colSpan={8-depth}>
								<h2 style={{"marginBottom": 0}}>{row.title}</h2>
								<div style={{"borderTop": "1px solid #666"}}></div>
							</td>
						</tr>,

						(() => {
							if(typeof row.children != "undefined" && row.children.length > 0)
							{
								return _this.renderRecursive(row.children, depth+1);
							}
							else
							{
								if(typeof row.accounts != "undefined" && row.accounts.length > 0)
								{
									return row.accounts.map(
										function (row, i)
										{
											return (
												<tr key={i}>
													<td colSpan={depth+1}>
														&nbsp;
													</td>
													<td colSpan={4-depth}><Link to={"/economy/account/" + row.account_number}>{row.account_number} {row.title}</Link></td>
													<td className="uk-text-right"><Currency value={row.balance_period} /></td>
													<td className="uk-text-right"><Currency value={0} /></td>
												</tr>
											);
										}
									);
								}
								else
								{
									return (
										<tr>
											<td colSpan={depth+1}>
												&nbsp;
											</td>
											<td colSpan={5-depth}>
												<em>Tom</em>
											</td>
										</tr>
									);
								}
							}
						})(),

						<tr>
							<td colSpan={depth}>
								&nbsp;
							</td>
							<td colSpan={5-depth} style={{"borderTop": "1px solid #666"}}>
								<h3 style={{"marginTop": 0}}>Summa {row.title}</h3>
							</td>
							<td style={{"borderTop": "1px solid #666"}} className="uk-text-right"><Currency value={row.balance_period} /></td>
							<td style={{"borderTop": "1px solid #666"}} className="uk-text-right"><Currency value={0} /></td>
						</tr>
					]
				);
			}
		);
	},

	render: function ()
	{
		if(this.state.fetched_data === false)
		{
			return (<p>Loading data</p>);
		}
		else
		{
			return (
				<div className="uk-width-1-1">
					<h2>Resultatrapport ÅRL</h2>
					<p>Räkneskapsår {this.state.data.financial_year}</p>
					<p>Period {this.state.data.period.from} - {this.state.data.period.to}</p>
					<p>Utskriven: {this.state.data.created}</p>
					<p>Senaste verifikation: {this.state.data.last_instruction}</p>

					<table style={{"width": "100%"}}>
						<thead>
							<tr>
								<td width="10">&nbsp;</td>
								<td width="30">&nbsp;</td>
								<td width="30">&nbsp;</td>
								<td width="30">&nbsp;</td>
								<td></td>
								<td className="uk-text-right">Period</td>
								<td className="uk-text-right">Period fg. år</td>
							</tr>
						</thead>
						<tbody>
							{this.renderRecursive(this.state.data.children)}
							<tr>
								<td style={{"borderTop": "1px solid #666"}} colSpan="5">Beräknat resultat</td>
								<td style={{"borderTop": "1px solid #666"}} className="uk-text-right"><Currency value={this.state.data.balance_period} /></td>
								<td style={{"borderTop": "1px solid #666"}} className="uk-text-right"><Currency value={this.state.data.balance_out} /></td>
							</tr>
						</tbody>
					</table>

				</div>
			);
		}

	}
});

module.exports = EconomyResultReportHandler