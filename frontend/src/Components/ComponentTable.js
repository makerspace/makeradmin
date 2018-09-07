import React from 'react';
import * as _ from "underscore";


export default class CollectionTable extends React.Component {
    
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


