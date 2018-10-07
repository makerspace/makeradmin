import Base from "./Base";
import * as _ from "underscore";

// In memory module representing a list of date periods.
export default class DatePeriodList extends Base {
    
    constructor(data) {
        super(data);
        this.unsubscribe = {};
    }
    
    remove(period) {
        this.periods = this.periods.filter(p => p !== period);
        this.unsubscribe[period.id]();
        delete this.unsubscribe[period.id];
    }
    
    add(period) {
        this.periods.push(period);
        this.unsubscribe[period.id] = period.subscribe(() => this.notify());
        this.notify();
    }
    
    replace(periods) {
        this.periods.length = 0;
        _.values(this.unsubscribe).map(u => u());
        this.unsubscribe = {};
        this.periods.push(...periods);
        periods.forEach(p => this.unsubscribe[p.id] = p.subscribe(() => this.notify()));
        this.notify();
    }
    
    isDirty(key) {
        if (key === 'periods') {
            return super.isDirty(key) || this.periods.some(p => p.isDirty());
        }
        
        if (key) {
            return super.isDirty(key);
        }
        
        return super.isDirty() || this.periods.some(p => p.isDirty());
    }
}

DatePeriodList.model = {
    attributes: {
        category: "",
        periods: [],
    },
};
