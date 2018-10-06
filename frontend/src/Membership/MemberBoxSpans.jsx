import React from 'react';
import {Link} from "react-router";
import Collection from "../Models/Collection";
import Span from "../Models/Span";
import {confirmModal} from "../message";
import CollectionTable from "../Components/CollectionTable";
import DateTimeShow from "../Components/DateTimeShow";
import DateShow from "../Components/DateShow";
import {assert, formatUtcDate, parseUtcDate, utcToday} from "../utils";
import DayPickerInput from 'react-day-picker/DayPickerInput';
import 'react-day-picker/lib/style.css';
import * as _ from "underscore";
import Base from "../Models/Base";


// In memory model representing a date period.
class DatePeriod extends Base {
    constructor(data) {
        super({...data, id: ++DatePeriod.counter});
    }
    
    getIsoStart() {
        return formatUtcDate(this.start);
    }
    
    setIsoStart(d) {
        this.start = parseUtcDate(d);
    }

    getIsoEnd() {
        return formatUtcDate(this.end);
    }
    
    setIsoEnd(d) {
        this.end = parseUtcDate(d);
    }
    
}

DatePeriod.counter = 0;

DatePeriod.model = {
    id: "id",
    attributes: {
        start: null,
        end: null,
    },
};

// In memory module representing a list of date periods.
class DatePeriodList extends Base {
    remove(period) {
        this.periods = this.periods.filter(p => p !== period);
    }
    
    add(period) {
        this.periods.push(period);
        this.notify();
    }
    
    replace(periods) {
        this.periods.length = 0;
        this.periods.push(...periods);
        this.notify();
    }
}

DatePeriodList.model = {
    attributes: {
        category: "",
        periods: [],
    },
};


class DatePeriodInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {start: utcToday(), end: utcToday()};
    }
    
    componentDidMount() {
        const {period} = this.props;
        period.subscribe(() => {
            this.setState({start: period.start, end: period.end});
        });
    }

    render() {
        const format = d => formatUtcDate(d);
        const {period} = this.props;
        const {start, end} = this.state;
        
        return (
            <span>
                <DayPickerInput value={start} formatDate={format} onDayChange={d => {if (d) period.start = d;}}/>
                -
                <DayPickerInput value={end} formatDate={format} onDayChange={d => {if (d) period.end = d;}}/>
            </span>
        );
    }
}


class DatePeriodListInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {periods: []};
    }

    componentDidMount() {
        const {periods} = this.props;
        periods.subscribe(() => {
            this.setState({periods: periods.periods});
        });
    }
    
    render() {
        const {category} = this.props.periods;
        const {periods} = this.state;
        
        return (
            <div>
                {periods.length}
                <h4>{category}</h4>
                {periods.map(p => <div key={p.id}><DatePeriodInput key={p.id} period={p}/><a onClick={() => this.props.periods.remove(p)} className="removebutton"><i className="uk-icon-trash"/></a></div>)}
                <button className="uk-button uk-button-small uk-button-success" onClick={() => {
                    this.props.periods.add(new DatePeriod({start: utcToday(), end: utcToday()}));
                }}>Add</button>
            </div>
        );
    }
}


// Return true if span1 end overlaps or is adjacent to span2 start.
const isConnected = (span1, span2) => {
    assert(span1.start <= span2.start);
    return span2.start - span1.end <= 24 * 3600 * 1000;
};


// Return assembled periods for non deleted spans in a category.
const filterPeriods = (items, category) => {
    const spans = items.filter(i => !i.deleted_at &&  i.span_type === category).sort((a, b) => a.startdate > b.startdate);
    const periods = [];
    
    while (!_.isEmpty(spans)) {
        let i = 1;
        while (i < spans.length && isConnected(spans[i - 1], spans[i])) ++i;
        const periodSpans = spans.splice(0, i);
        periods.push(new DatePeriod({
                                    start: new Date(Math.min(...periodSpans.map(s => s.start))),
                                    end: new Date(Math.max(...periodSpans.map(s => s.end))),
                                }));
    }
    return periods;
};


class MemberBoxSpans extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Span, filter: {member_id: props.params.member_id}, pageSize: 0});
        this.categories = [
            new DatePeriodList({category: 'labaccess'}),
            new DatePeriodList({category: 'special_labaccess'}),
            new DatePeriodList({category: 'membership'}),
        ];
        this.state = {items: []};
    }

    componentDidMount() {
        this.collection.subscribe(({items}) => {
            this.categories.forEach(periods => periods.replace(filterPeriods(items, periods.category)));
            this.setState({items});
        });
    }
    
    render() {
        const deleteItem = item => confirmModal(item.deleteConfirmMessage()).then(() => item.del()).then(() => this.collection.fetch(), () => null);
        
        return (
            <div className="uk-margin-top">
                <h2>Medlemsperioder</h2>
                {this.categories.map(periods => <DatePeriodListInput key={periods.category} periods={periods}/>)}
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
