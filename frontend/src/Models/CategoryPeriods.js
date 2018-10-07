import Base from "./Base";
import * as _ from "underscore";
import {mergePeriods} from "./Span";

// In memory module representing a list of date periods in the same span category.
export default class CategoryPeriods extends Base {
    
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

    // Should be called after edit and before save to eliminate any overlapping periods.
    merge() {
        this.periods.sort((a, b) => a.start > b.start);
        this.replace(mergePeriods(this.periods));
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
    
    isValid() {
        return this.periods.every(p => p.isValid());
    }
    
    canSave() {
        return this.isDirty() && this.isValid();
    }
}

CategoryPeriods.model = {
    attributes: {
        category: "",
        periods: [],
    },
};
