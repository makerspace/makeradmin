import Base from "./Base";

// In memory model representing a date period.
export default class DatePeriod extends Base<DatePeriod> {
    static counter: number = 0;
    start!: Date | null;
    end!: Date | null;

    static model = {
        id: "id",
        attributes: {
            start: null,
            end: null,
        },
    };

    constructor(data: Partial<DatePeriod> | null) {
        super({ ...data, id: ++DatePeriod.counter });
    }

    isValid(key?: "start" | "end") {
        if (key && !this[key]) {
            return false;
        }
        return (
            this.start !== null && this.end !== null && this.start <= this.end
        );
    }

    override canSave() {
        return this.isDirty() && this.isValid();
    }
}
