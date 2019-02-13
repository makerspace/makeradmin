import React from 'react';
import Span from "../Models/Span";
import * as _ from "underscore";


class SpanShow extends React.Component {
    
    constructor(props) {
        super(props);
        const {span_id} = props.params;
        this.span = Span.get(span_id);
        this.state = {data: {}};
    }
    
    componentDidMount() {
        this.unsubscribe = this.span.subscribe(() => this.setState({data: this.span.saved}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {data} = this.state;

        return (
            <div>
                <h2>Medlemsperiod {data.span_id}</h2>
                <dl className="uk-description-list">
                    {_.keys(data).map(key => <div key={key}><dt>{key}:</dt><dd>{data[key]}</dd></div>)}
                </dl>
            </div>
        );
    }
}

export default SpanShow;
