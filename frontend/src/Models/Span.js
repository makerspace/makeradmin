import Base from './Base';

// Spans are startdate - enddate (inclusive - inclusive) but some spans are overlapping.
export default class Span extends Base {
    deleteConfirmMessage() {
        return `Are you sure you want to delete span ${this.id}?`;
    }
    
    start() {
        return new Date(this.startdate + "T00:00:00.000Z");
    }
    
    end() {
        return new Date(this.enddate + "T23:59:59.999Z");
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