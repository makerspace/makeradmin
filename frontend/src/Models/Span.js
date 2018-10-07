import Base from './Base';
import {assert, parseUtcDate} from "../utils";
import DatePeriod from "./DatePeriod";
import * as _ from "underscore";

// Spans are startdate - enddate (inclusive - inclusive) but some spans are overlapping.
export default class Span extends Base {
    deleteConfirmMessage() {
        return `Are you sure you want to delete span ${this.id}?`;
    }
    
    get start() {
        return new Date(parseUtcDate(this.startdate));
    }
    
    get end() {
        return new Date(parseUtcDate(this.enddate));
    }
}

Span.model = {
    id: "span_id",
    root: "/membership/span",
    attributes: {
        span_id: 0,
        member_id: null,
        startdate: null,
        enddate: null,
        span_type: "",
        created_at: null,
        creation_reason: "",
        deleted_at: null,
        deletion_reason: null,
        // extend="member"
        member_number: 0,
        firstname: "",
        lastname: "",
    },
};


// Return true if span1 end overlaps or is adjacent to span2 start.
export const isConnected = (span1, span2) => {
    assert(span1.start <= span2.start);
    return span2.start - span1.end <= 24 * 3600 * 1000;
};


// Return assembled periods for non deleted spans in a category.
export const filterPeriods = (items, category) => {
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


