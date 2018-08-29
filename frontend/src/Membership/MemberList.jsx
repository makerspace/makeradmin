import React from 'react';
import { Link } from 'react-router';
import Date from '../Components/Date';
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import * as _ from "underscore";


// TODO Delete
// TODO Snurr


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
								<input ref="search" tabIndex="1" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord"
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
        const {item, removeItem} = this.props;
        return (
			<tr>
				<td><Link to={"/membership/members/" + item.member_id}>{item.member_number}</Link></td>
				<td>{item.firstname}</td>
				<td>{item.lastname}</td>
				<td>{item.email}</td>
				<td><Date date={item.created_at}/></td>
                <td><a onClick={() => removeItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
			</tr>
        );
    }
}


class Table extends React.Component {
    
    constructor(props) {
        super(props);
        this.state = {sort: {key: null, order: 'up'}};
    }
    
    renderHeading(c, i) {
        const sortState = this.state.sort;
        const {onSort} = this.props;
        if (c.title) {
            let title;
            if (c.sort) {
                const sortIcon = <i className={"uk-icon-angle-" + sortState.order}/>;
                const onClick = () => {
                    const sort = {key: c.sort, order: sortState.key === c.sort && sortState.order === 'down' ? 'up' : 'down'};
                    onSort(sort);
                    this.setState({sort});
                };
                title = (
                    <a data-sort={c.sort} onClick={onClick}>
                        {c.title} {c.sort === sortState.key ? sortIcon : ''}
                    </a>);
            }
            else {
                title = c.title;
            }
            return <th key={i} className={c.class}>{title}</th>;
        }
        return <th key={i}/>;
    }

    renderPagination() {
        const {page, updatePage} = this.props;
        if (!page.count || page.count <= 1) {
            return "";
        }
        
        return (
            <ul className="uk-pagination">
                {_.range(1, page.count + 1).map(i => {
                    if (i === page.index) {
                        return <li key={i} className="uk-active"><span>{i}</span></li>;
                    }
                    return <li key={i}><a href="#" onClick={() => updatePage(i)}>{i}</a></li>;
                })}
            </ul>
        );
    }
    
    render() {
        const {items, removeItem, rowComponent, columns} = this.props;
        
        const rows = items.map((item, i)  => React.createElement(rowComponent, {item, removeItem, key: i}));
        const headers = columns.map((c, i) => this.renderHeading(c, i));
        const pagination = this.renderPagination();
        const loadinClass = "";
        const loading = "";
        
        return (
            <div>
                {pagination}
                <div style={{position: "relative", "clear": "both"}}>
                    <table className={"uk-table uk-table-condensed uk-table-striped uk-table-hover" + loadinClass}>
                        <thead><tr>{headers}</tr></thead>
						<tbody>{rows}</tbody>
					</table>
					{loading}
				</div>
				{pagination}
			</div>
        );
    }
}


class MemberList extends React.Component {

    constructor(props) {
        super(props);
        this.state = {items: [], page: {}};
        this.collection = new Collection({type: Member, onUpdate: ({items, page}) => this.setState({items, page})});
    }

    removeItem(item) {
        console.info("remove item", item);
    }
    
    render() {
        const columns = [
            {title: "#", sort: "member_id"},
			{title: "Förnamn", sort: "firstname"},
			{title: "Efternamn", sort: "lastname"},
			{title: "E-post", sort: "email"},
			{title: "Blev medlem", sort: "created_at"},
			{title: ""},
		];
        
        const {items, page} = this.state;
  
		return (
			<div>
				<h2>Medlemmar</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
				<Link to="/membership/membersx/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny medlem</Link>

				<SearchBox onChange={filters => this.collection.updateFilter(filters)} />
                <Table
                    onSort={sort => this.collection.updateSort(sort)}
                    rowComponent={Row}
                    columns={columns}
                    items={items}
                    removeItem={(item) => this.removeItem(item)}
                    page={page}
                    updatePage={index => this.collection.updatePage(index)}
                />
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