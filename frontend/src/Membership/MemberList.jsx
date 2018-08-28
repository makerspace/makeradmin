import React from 'react';
import { Link } from 'react-router';
import { get } from "../gateway";


class SearchBox extends React.Component {
    
    constructor(props) {
        super(props);
    }
    
	render() {
		return (
			<div className="filterbox">
				<div className="uk-grid">
					<div className="uk-width-2-3">
						<form className="uk-form">
							<div className="uk-form-icon">
								<i className="uk-icon-search"/>
								<input ref="search" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord"
                                       onChange={() => this.props.onChange({search: this.refs.search.value})} />
							</div>
						</form>
					</div>
				</div>
			</div>
		);
	}
}


class Row extends React.Component {
    
    render() {
        const {item} = this.props;
        return <tr><td>{item.member_id}</td></tr>;
    }
}


class Table extends React.Component {
    
    render() {
        const {items, rowComponent} = this.props;
        
        const rows = items.map((item, i)  => React.createElement(rowComponent, {item, key: i}));
        
        return <table><tbody>{rows}</tbody></table>;
    }
}


class MemberList extends React.Component {

    constructor(props) {
        super(props);
        this.state = {members: []};
        this.filters = {};
        this.sort = null;
        this.fetch();
    }

    sort(key) {
        this.sort = key;
        this.fetch();
    }
    
    filter(filters) {
        this.filters = filters;
        this.fetch();
    }
    
    fetch() {
        get("/membership/member?page=1&sort_by=&sort_order=asc&per_page=25", data => {
            this.setState({members: data.data});
        });
    }
    
	render() {
		return (
			<div>
				<h2>Medlemmar</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
				<Link to="/membership/membersx/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny medlem</Link>

				<SearchBox onChange={(filters) => this.setState({filters})} />
                <Table columns={[]} onSort={() => 1} rowComponent={Row} items={this.state.members}/>
			</div>
		);
	}

}

export default MemberList;

/*

import MemberCollection from './Collections/Member';
import Members from './Components/Tables/Members';

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(member)
	{
		return "Are you sure you want to remove member \"" + member.firstname + " " + member.lastname + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Ett fel uppstod vid borttagning av medlem", {timeout: 0, status: "danger"});
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/membership/members/" + row.member_id}>{row.member_number}</Link></td>
				<td>-</td>
				<td>{row.firstname}</td>
				<td>{row.lastname}</td>
				<td>{row.email}</td>
				<td><DateField date={row.created_at} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/membership/members/" + row.member_id}><i className="uk-icon-cog"></i> Redigera medlem</Link>
						{this.removeButton(i, "Ta bort medlem")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "member_id",
			},
			{
				title: "Kön",
			},
			{
				title: "Förnamn",
				sort: "firstname",
			},
			{
				title: "Efternamn",
				sort: "lastname",
			},
			{
				title: "E-post",
				sort: "email",
			},
			{
				title: "Blev medlem",
				sort: "created_at",
			},
			{
				title: "",
			},
		];
	},
});


*/