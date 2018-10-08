/* eslint-env jest */
import {addToDate, formatUtcDate, utcToday} from "../../utils";
import {calculateSpanDiff, DAY_MILLIS} from "../Span";
import Span from "../Span";
import DatePeriod from "../DatePeriod";
import * as _ from "underscore";


const today = utcToday();


const day = offsetDays => addToDate(today, offsetDays * DAY_MILLIS);


const createSpan = (id, startOffsetDays, endOffsetDays) => {
    return new Span({
        id,
        startdate: formatUtcDate(day(startOffsetDays)),
        enddate: formatUtcDate(day(endOffsetDays)),
        span_type: 'labaccess',
    });
};


const createPeriod = (startOffsetDays, endOffsetDays) =>
    new DatePeriod({
        start: day(startOffsetDays),
        end: day(endOffsetDays),
    });
    

describe("calculateSpanDiff", () => {

    const a = 'a';
    const b = 'b';
    const c = 'c';
    
    expect.extend({
        diffToMatch([spanOffsets, periodOffsets], expectedDeleteIds, expectedAddSpans) {
            const deleteSpans = [];
            const addSpans = [];
            const spans = spanOffsets.map(([id, s, e]) => createSpan(id, s, e));
            const periods = periodOffsets.map(([s, e]) => createPeriod(s, e));
            
            const str = "diff from spans " + JSON.stringify(spanOffsets) + " and periods " + JSON.stringify(periodOffsets) + ", expected";
            
            calculateSpanDiff({
                items: spans,
                categoryPeriods: {periods, category: "labaccess"},
                member_id: 1,
                deleteSpans,
                addSpans
            });
        
            const actualDeleteIds = deleteSpans.map(s => s.id);
            if (!_.isEqual(expectedDeleteIds, actualDeleteIds)) {
                return {
                    message: () => `${str} deleted ids to be ${JSON.stringify(expectedDeleteIds)}, was ${JSON.stringify(actualDeleteIds)}`,
                    pass: false,
                };
            }
            const actualAddSpans = addSpans.map(s => [(s.start - today) / DAY_MILLIS, (s.end - today) / DAY_MILLIS]);
            if (!_.isEqual(expectedAddSpans, actualAddSpans)) {
                return {
                    message: () => `${str} add spans to be ${JSON.stringify(expectedAddSpans)}, was ${JSON.stringify(actualAddSpans)}`,
                    pass: false,
                };
            }
            
            return {
                message: () => `expected diff to be deletes ${JSON.stringify(expectedDeleteIds)} and adds ${JSON.stringify(expectedAddSpans)}`,
                pass: true,
            };
        }
    });

    test('calculates no changes for spans equal to period', () => {
        expect([[[a, 0, 4]], [[0, 4]]]).diffToMatch([], []);
    });
    
});
