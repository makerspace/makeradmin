import React from 'react';
import DatePeriodList from "../Models/DatePeriodList";
import DatePeriodListInput from "../Components/DatePeriodListInput";
import {filterPeriods} from "../Models/Span";


export default class MembershipPeriodsInput extends React.Component {
    constructor(props) {
        super(props);
        this.unsubscribe = [];
        this.categories = [
            new DatePeriodList({category: 'labaccess'}),
            new DatePeriodList({category: 'membership'}),
            new DatePeriodList({category: 'special_labaccess'}),
        ];
        this.state = {showHistoric: true, saveDisabled: true};
    }

    componentDidMount() {
        this.unsubscribe.push(this.props.spans.subscribe(({items}) => {
            this.categories.forEach(periods => periods.replace(filterPeriods(items, periods.category)));
        }));
        this.categories.forEach(category => {
            this.unsubscribe.push(category.subscribe(() => this.setState({saveDisabled: !this.categories.some(c => c.isDirty())})));
        });
    }

    componentWillUnmount() {
        this.unsubscribe.forEach(u => u());
    }

    render() {
        const {showHistoric, saveDisabled} = this.state;
        
        const onSave = () => {
            const {deleteSpans, addSpans} = calculateSpanDiff({spans: this.props.items, categories: this.categories});
            console.info("delete", deleteSpans);
            console.info("add", addSpans);
        };
        
        return (
            <form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                <label className="uk-label" htmlFor="showHistoric">Visa historiska</label>
                <input id="showHistoric" className="uk-checkbox" type="checkbox" checked={showHistoric} onChange={e => this.setState({showHistoric: e.target.checked})}/>
                {this.categories.map(periods => <DatePeriodListInput key={periods.category} periods={periods} showHistoric={showHistoric}/>)}
                <button disabled={saveDisabled} className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save"/> Spara</button>
            </form>
        );
    }
}


