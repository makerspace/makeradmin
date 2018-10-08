import Base from './Base';
import {addToDate, assert, formatUtcDate, parseUtcDate, utcToday} from "../utils";
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

// TODO Most of the functions here needs some tests. Test a lot with one day spans.

export const DAY_MILLIS = 24 * 3600 * 1000;


// Find overlapping and adjacent periods/spans, needs to be sorted on start.
export const isConnected = (a, b) => {
    assert(a.start <= b.start);
    return b.start - a.end <= DAY_MILLIS;
};


// Merge overlapping periods/spans and return new period list, input needs to be sorted on start.
export const mergePeriods = toMergePeriods => {
    const oldPeriods = toMergePeriods.slice();
    const newPeriods = [];
    while (!_.isEmpty(oldPeriods)) {
        let i = 1;
        while (i < oldPeriods.length && isConnected(oldPeriods[i - 1], oldPeriods[i])) ++i;
        const periods = oldPeriods.splice(0, i);
        newPeriods.push(new DatePeriod({
                                           start: new Date(Math.min(...periods.map(s => s.start))),
                                           end: new Date(Math.max(...periods.map(s => s.end))),
                                       }));
    }
    return newPeriods;
};


// Filter not deleted spans for one category, return sorted.
export const filterCategory = (spans, category) =>
    spans.filter(i => !i.deleted_at &&  i.span_type === category).sort((a, b) => a.startdate > b.startdate);


// Return assembled periods for non deleted spans in a category.
export const filterPeriods = (spans, category) =>
    mergePeriods(filterCategory(spans, category));


// TODO Remove
const log = console.info;
const day = dt => (dt - utcToday()) / DAY_MILLIS;
const log_add = (msg, start, end) => {
    log(msg, day(start), day(end));
};


// Given the category periods and spans, calculate additions and deletions needed and add them to respective lists.
// Spans may have overlaps, periods may not overlap each other.
export const calculateSpanDiff = ({items, categoryPeriods, member_id, deleteSpans, addSpans}) => {
    const {periods, category} = categoryPeriods;
    const spans = filterCategory(items, category);
    // Walk trough both lists and decide what spans to delete/keep/add.
    
    let pi = 0;
    let si = 0;
    
    const addSpan = (start, end) => {
        assert(start <= end);
        addSpans.push(new Span({
                                   startdate: formatUtcDate(start),
                                   enddate: formatUtcDate(end),
                                   span_type: category,
                                   member_id,
                               }));
    };
    
    const deleteSpan = span => {
        assert(span.id);
        deleteSpans.push(span);
    };
    
    while (true) {
        log("top si", si, "pi", pi);
        if (si === spans.length) {
            // Out of spans, add rest of periods as spans.
            for (let i = pi; i < periods.length; ++i) {
                const {start, end} = periods[i];
                log_add("out of spans", start, end);
                addSpan(start, end);
            }
            return;
        }

        if (pi === periods.length) {
            // Out of periods, delete rest of spans.
            log("deleting all from", si);
            spans.slice(si).forEach(s => deleteSpan(s));
            return;
        }

        const period = periods[pi];
        
        // Remove all spans that ends before the next period.
        while (si < spans.length && spans[si].end < period.start) {
            log("delete, ends berfore peropd", spans[si].id);
            deleteSpan(spans[si]);
            ++si;
        }
        
        // Remove all spans overlapping start of period.
        while (si < spans.length && spans[si].start < period.start && spans[si].end >= period.start) {
            log("delete, overlaps start of period", spans[si].id);
            deleteSpan(spans[si]);
            ++si;
        }
        
        if (si === spans.length) {
            continue;
        }

        log("mid, si", si);
        
        // Go through all spans with start inside the period, make sure there is no inside gaps, spans are not sorted
        // by end date.
        let gapStart = period.start;
        while (si < spans.length && spans[si].start <= period.end && gapStart < period.end) {
            log("gapStart", day(gapStart));
            const span = spans[si];
            if (span.end > period.end || span.end < gapStart) {
                // Span overlaps end, or it does not help filling the gap, delete and ignore.
                log("delete, span ends after period", span.id);
                deleteSpan(span);
            }
            else if (gapStart.getTime() === span.start.getTime()) {
                // Keep span.
                log("keep span ", day(span.start), day(span.end));
                gapStart = addToDate(span.end, DAY_MILLIS);
            }
            else {
                // Add span to fill period to start of span, then keep span.
                log("fill start of period ", day(gapStart), day(addToDate(span.start, -DAY_MILLIS)));
                addSpan(gapStart, addToDate(span.start, -DAY_MILLIS));
                gapStart = addToDate(span.start, DAY_MILLIS);
            }
            ++si;
        }
        log("near end, si", si);
        // Fill the last gap if there is one.
        if (gapStart <= period.end) {
            log_add("fill gap to end of period,", gapStart, period.end);
            addSpan(gapStart, period.end);
        }
        
        ++pi;
    }
};



