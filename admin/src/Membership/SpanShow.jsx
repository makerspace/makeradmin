import React, { useState, useEffect } from "react";
import Span from "../Models/Span";
import * as _ from "underscore";

export default function SpanShow(props) {
    const { span_id } = props.match.params;
    const [data, setData] = useState({});

    const span = Span.get(span_id);

    useEffect(() => {
        const unsubscribe = span.subscribe(() => setData(span.saved));
        
        // Cleanup subscription on unmount
        return () => unsubscribe();
    }, [span]);

    return (
        <div>
            <h2>Medlemsperiod {data.span_id}</h2>
            <dl className="uk-description-list">
                {_.keys(data).map((key) => (
                    <div key={key}>
                        <dt>{key}:</dt>
                        <dd>{data[key]}</dd>
                    </div>
                ))}
            </dl>
        </div>
    );
}
