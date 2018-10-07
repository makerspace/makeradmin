import Base from "./Base";

// In memory model representing a date period.
export default class DatePeriod extends Base {
    constructor(data) {
        super({...data, id: ++DatePeriod.counter});
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
