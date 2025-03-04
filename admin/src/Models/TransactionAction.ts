import { ActionTypes } from "Models/ProductAction";
import Base from "./Base";

export enum Status {
    pending = "pending",
    completed = "completed",
    cancelled = "cancelled",
}

export default class TransactionAction extends Base<TransactionAction> {
    content_id!: number;
    action_type!: ActionTypes;
    value!: number;
    status!: Status;
    completed_at!: Date | null;

    static model = {
        root: "/webshop/transaction_action",
        id: "id",
        attributes: {
            value: 0,
            action_type: ActionTypes.ADD_LABACCESS_DAYS,
            status: Status.pending,
            completed_at: null,
            content_id: -1,
            deleted_at: null,
        },
    };

    statusEmoji(): string {
        switch (this.status) {
            case Status.pending:
                return "⏳";
            case Status.completed:
                return "✅";
            case Status.cancelled:
                return "❌";
        }
    }
}
