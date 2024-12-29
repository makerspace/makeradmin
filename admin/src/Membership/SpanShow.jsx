import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import * as _ from "underscore";
import Span from "../Models/Span";

function SpanShow() {
    const { span_id } = useParams();
    const spanInstance = useMemo(() => Span.get(span_id), [span_id]);
    const [data, setData] = useState({});

    useEffect(() => {
        const unsubscribe = spanInstance.subscribe(() => {
            setData(spanInstance.saved);
        });

        return () => {
            unsubscribe();
        };
    }, [spanInstance]);

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

export default SpanShow;
