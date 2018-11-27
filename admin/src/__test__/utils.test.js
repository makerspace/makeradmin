/* eslint-env jest */

import {dateTimeToStr, dateToStr} from "../utils";

describe("timestamp string from server", () => {
    test('is coverted to nice date string', () => {
        expect(dateToStr("2018-10-26T18:44:40Z")).toBe("2018-10-26");
    });
    
    test('is converted to nice datetime string in winter time', () => {
        expect(dateTimeToStr("2018-11-10T18:44:40Z")).toBe("2018-11-10 19:44:40");
    });

    test('is converted to nice datetime string in summer time', () => {
        expect(dateTimeToStr("2018-10-10T18:44:40Z")).toBe("2018-10-10 20:44:40");
    });
});
