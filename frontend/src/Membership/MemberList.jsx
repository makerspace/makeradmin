import React from 'react';
import { Link } from 'react-router';
import Date from '../Components/Date';
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import * as _ from "underscore";
import Loading from '../Components/Loading';


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


class CollectionTable extends React.Component {
    
    constructor(props) {
        super(props);
        this.state = {sort: {key: null, order: 'up'}, items: [], page: {}, loading: true};
    }
    
    componentDidMount() {
        const {collection} = this.props;
        this.unsubscribe = collection.subscribe(({page, items}) => this.setState({page, items, loading: false}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    renderHeading(c, i) {
        const sortState = this.state.sort;
        const {collection} = this.props;
        
        if (c.title) {
            let title;
            if (c.sort) {
                const sortIcon = <i className={"uk-icon-angle-" + sortState.order}/>;
                const onClick = () => {
                    const sort = {key: c.sort, order: sortState.key === c.sort && sortState.order === 'down' ? 'up' : 'down'};
                    this.setState({sort, loading: true});
                    collection.updateSort(sort);
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
        const {collection} = this.props;
        const {page} = this.state;
        
        if (!page.count || page.count <= 1) {
            return "";
        }
        
        return (
            <ul className="uk-pagination">
                {_.range(1, page.count + 1).map(i => {
                    if (i === page.index) {
                        return <li key={i} className="uk-active"><span>{i}</span></li>;
                    }
                    return <li key={i}><a href="#" onClick={() => {
                        this.setState({loading: true});
                        collection.updatePage(i);
                    }}>{i}</a></li>;
                })}
            </ul>
        );
    }
    
    render() {
        const {collection, rowComponent, columns} = this.props;
        const {items, loading} = this.state;
        
        const rows = items.map((item, i)  => React.createElement(rowComponent, {item, removeItem: () => collection.removeItem(item), key: i}));
        const headers = columns.map((c, i) => this.renderHeading(c, i));
        const pagination = this.renderPagination();
			
        return (
            <div>
                {pagination}
                <div style={{position: "relative", "clear": "both"}}>
                    <table className={"uk-table uk-table-condensed uk-table-striped uk-table-hover" + (loading ? " backboneTableLoading" : "")}>
                        <thead><tr>{headers}</tr></thead>
						<tbody>{rows}</tbody>
					</table>
                    {loading ?
                     <div className="loadingOverlay">
                         <div className="loadingWrapper">
                             <span><i className="uk-icon-refresh uk-icon-spin"/> Hämtar data...</span>
                         </div>
                     </div>  : ''}
				</div>
				{pagination}
			</div>
        );
    }
}


class MemberList extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Member});
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
        
		return (
			<div>
				<h2>Medlemmar</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
				<Link to="/membership/membersx/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny medlem</Link>

				<SearchBox onChange={filters => this.collection.updateFilter(filters)} />
                <CollectionTable
                    rowComponent={Row}
                    collection={this.collection}
                    columns={columns}
                />
			</div>
		);
	}
}

export default MemberList;
