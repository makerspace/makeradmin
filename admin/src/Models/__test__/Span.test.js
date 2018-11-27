/* eslint-env jest */
import {addToDate, formatUtcDate, utcToday} from "../../utils";
import {calculateSpanDiff, DAY_MILLIS} from "../Span";
import Span from "../Span";
import DatePeriod from "../DatePeriod";
import * as _ from "underscore";


const today = utcToday();


const day = offsetDays => addToDate(today, offsetDays * DAY_MILLIS);


const createSpan = (span_id, startOffsetDays, endOffsetDays) => {
    return new Span({
        span_id,
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
        expect([[[a, 0, 0]], [[0, 0]]]).diffToMatch([], []);
        expect([[[a, 0, 2], [b, 3, 4]], [[0, 4]]]).diffToMatch([], []);
        expect([[[a, 0, 2], [b, 2, 4]], [[0, 4]]]).diffToMatch([], []);
        expect([[[a, 0, 2], [b, 4, 6]], [[0, 2], [4, 6]]]).diffToMatch([], []);
    });

    test('calculates not needed spans deleted, no change in period', () => {
        expect([[[a, 0, 4], [b, 1, 2]], [[0, 4]]]).diffToMatch([b], []);
        expect([[[a, 0, 4], [b, 1, 2], [c, 2, 4]], [[0, 4]]]).diffToMatch([b, c], []);
        expect([[[a, 0, 0], [b, 0, 0]], [[0, 0]]]).diffToMatch([b], []);
        expect([[[a, 0, 0], [b, 0, 0], [c, 1, 1]], [[0, 1]]]).diffToMatch([b], []);
    });

    test('calculates excessive spans outside period to be removed', () => {
        expect([[[a, 0, 0], [b, 2, 6], [c, 8, 8]], [[2, 6]]]).diffToMatch([a, c], []);
        expect([[[a, 0, 2], [b, 2, 6], [c, 6, 8]], [[2, 6]]]).diffToMatch([a, c], []);
        expect([[[a, 1, 1], [b, 2, 6], [c, 7, 7]], [[2, 6]]]).diffToMatch([a, c], []);
        expect([[[a, 1, 9], [b, 2, 6]], [[2, 6]]]).diffToMatch([a], []);
        expect([[[a, 2, 6], [b, 7, 7], [c, 8, 10]], [[2, 6], [8, 10]]]).diffToMatch([b], []);
    });

    test('calculates adds spans needed to cover periods', () => {
        expect([[], [[2, 6]]]).diffToMatch([], [[2, 6]]);
        expect([[[a, 2, 2]], [[2, 6]]]).diffToMatch([], [[3, 6]]);
        expect([[[a, 2, 2], [b, 6, 6]], [[2, 6]]]).diffToMatch([], [[3, 5]]);
        expect([[[a, 2, 2], [b, 4, 4], [c, 6, 6]], [[2, 6]]]).diffToMatch([], [[3, 3], [5, 5]]);
        expect([[[a, 2, 5], [b, 6, 6], [c, 8, 8]], [[2, 6], [8, 12]]]).diffToMatch([], [[9, 12]]);
    });

    test('calculates both adds and deletes needed', () => {
        expect([[[a, 1, 6]], [[2, 6]]]).diffToMatch([a], [[2, 6]]);
        expect([[[a, 1, 2], [b, 6, 7]], [[2, 6]]]).diffToMatch([a, b], [[2, 6]]);
        expect([[[a, 2, 2], [b, 6, 7]], [[2, 6]]]).diffToMatch([b], [[3, 6]]);
        expect([[[a, 2, 5], [b, 7, 12]], [[2, 6], [8, 12]]]).diffToMatch([b], [[6, 6], [8, 12]]);
    });
    
    test('a bit longer periods in case of month or year issues', () => {
        expect([[], [[-800, 800]]]).diffToMatch([], [[-800, 800]]);
        expect([[[a, -800, 0]], [[-800, 800]]]).diffToMatch([], [[1, 800]]);
        expect([[[a, -801, 0], [b, -100, 100]], [[-800, 800]]]).diffToMatch([a], [[-800, -101], [101, 800]]);
    });

    
});

