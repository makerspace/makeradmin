import Base from "./Base";

// In memory module representing a list of date periods.
export default class DatePeriodList extends Base {

    remove(period) {
        this.periods = this.periods.filter(p => p !== period);
    }
    
    add(period) {
        this.periods.push(period);
        this.notify();
    }
    
    replace(periods) {
        this.periods.length = 0;
        this.periods.push(...periods);
        this.notify();
    }
}

DatePeriodList.model = {
    attributes: {
        category: "",
        periods: [],
    },
};
