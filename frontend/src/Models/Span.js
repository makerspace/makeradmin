import Base from './Base';
import {parseUtcDate} from "../utils";

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