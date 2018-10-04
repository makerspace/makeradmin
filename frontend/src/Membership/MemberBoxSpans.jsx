import React from 'react';
import {Link} from "react-router";
import Collection from "../Models/Collection";
import Span from "../Models/Span";
import {confirmModal} from "../message";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import DateShow from "../Components/DateShow";
import {assert, formatUtcDate} from "../utils";
import * as _ from "underscore";


// Collection of spans of the same type that creates an unbroken period in time, overlaps may exist.
class Period {
    
    constructor(spans) {
        this.spans = spans;
        for (let i = 1; i < spans.length; ++i) {
            assert(spans[i - 1].start() <= spans[i].start());
        }
    }
    
    end() {
        return new Date(Math.max(...this.spans.map(s => s.end())));
    }
    
    start() {
        return new Date(Math.min(...this.spans.map(s => s.start())));
    }
}


// Return true if span1 end overlaps or is adjacent to span2 start.
const isConnected = (span1, span2) => {
    assert(span1.start() <= span2.start());
    return span2.start() - span1.end() <= 1;
};


// Return assembled periods for non deleted spans in a category.
const filterPeriods = (items, category) => {
    const spans = items.filter(i => !i.deleted_at &&  i.span_type === category).sort((a, b) => a.startdate > b.startdate);
    const res = [];
    let current = [];
    for (let i = 0; i < spans.length; ++i) {
        const last = current[current.length - 1];
        const span = spans[i];
        if (_.isEmpty(current) || isConnected(last, span)) {
            current.push(span);
        }
        else {
            res.push(new Period(current));
            current = [];
        }
    }
    if (!_.isEmpty(current)) {
        res.push(new Period(current));
    }
    console.info(category, res);
    return res;
};


class MemberBoxSpans extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Span, filter: {member_id: props.params.member_id}, pageSize: 0});
        this.state = {items: []};
    }

    componentDidMount() {
        this.collection.subscribe(({items}) => {
            this.setState({items});
        });
    }
    
    render() {
        const {items} = this.state;
        
        const deleteItem = item => confirmModal(item.deleteConfirmMessage()).then(() => item.del()).then(() => this.collection.fetch(), () => null);
        
        const renderPeriods = periods => <ul>{periods.map((p, i) => <li key={i}>{formatUtcDate(p.start())} - {formatUtcDate(p.end())}</li>)}</ul>;
        
        const renderCategory = category => <div key={category}><strong>{category}:</strong>{renderPeriods(filterPeriods(items, category))}</div>;
        
        return (
            <div className="uk-margin-top">
                <h2>Medlemsperioder</h2>
                {["labaccess", "special_labaccess", "membership"].map(renderCategory)}
                <h2>Spans</h2>
                <CollectionTable
                    collection={this.collection}
                    columns={[
                        {title: "#", sort: "span_id"},
                        {title: "Typ", sort: "span_type"},
                        {title: "Skapad", sort: "created_at"},
                        {title: ""},
                        {title: "Raderad", sort: "deleted_at"},
                        {title: "Start", sort: "startdate"},
                        {title: "Slut", sort: "enddate"},
                    ]}
                    rowComponent={({item}) => (
                        <tr>
                            <td><Link to={"/membership/spans/" + item.id}>{item.id}</Link></td>
                            <td><Link to={"/membership/spans/" + item.id}>{item.span_type}</Link></td>
                            <td><DateTimeShow date={item.created_at}/></td>
                            <td>{item.creation_reason}</td>
                            <td><DateTimeShow date={item.deleted_at}/></td>
                            <td><DateShow date={item.startdate}/></td>
                            <td><DateShow date={item.enddate}/></td>
                            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}


export default MemberBoxSpans;
