import Cart from "./cart";
import { member_t } from "./member_common";
import { Transaction, TransactionItem } from "./payment_common";
function format_receipt_status(transaction_status: string) {
    switch (transaction_status) {
        case "pending":
            return "Ej bekräftad";
        case "completed":
            return "";
        case "failed":
            return "Misslyckad";
    }
    return "Okänd status";
}

const ReceiptItem = ({ item }: { item: TransactionItem }) => {
    return (
        <>
            <a
                className="product-title"
                href={`/shop/product/${item.product.id}`}
            >
                {item.product.name}
            </a>
            <span className="receipt-item-count">
                {item.count} {item.product.unit}
            </span>
            <span className="receipt-item-amount">
                {Cart.formatCurrency(Number(item.amount))}
            </span>
        </>
    );
};

export const Receipt = ({
    transaction,
    member,
    detailed,
}: {
    transaction: Transaction;
    member?: member_t;
    detailed: boolean;
}) => {
    return (
        <div className={`history-item history-item-${transaction.status}`}>
            <a
                className="receipt-header"
                href={`/shop/receipt/${transaction.id}`}
            >
                <span>Kvitto {transaction.id}</span>
                <span className="receipt-date">
                    {new Date(transaction.created_at).toLocaleDateString(
                        "sv-SE",
                        {
                            year: "numeric",
                            month: "numeric",
                            day: "numeric",
                            hour: detailed ? "numeric" : undefined,
                            minute: detailed ? "numeric" : undefined,
                        },
                    )}
                </span>
            </a>
            <div className="receipt-items">
                {transaction.contents.map((item) => (
                    <ReceiptItem item={item} />
                ))}
            </div>
            <div className="receipt-amount">
                {transaction.status === "completed" && detailed ? (
                    <span>Summa</span>
                ) : (
                    <span className="receipt-payment-status">
                        {format_receipt_status(transaction.status) ||
                            (detailed ? "Summa" : "")}
                    </span>
                )}
                <span className="receipt-amount-value">
                    {Cart.formatCurrency(Number(transaction.amount))}
                </span>
            </div>
            {member !== undefined && detailed && (
                <div className="receipt-items">
                    <>
                        <span className="product-title">{`#${member.member_number} - ${member.firstname} ${member.lastname}`}</span>
                        <span className="receipt-item-amount"></span>
                    </>
                </div>
            )}
        </div>
    );
};
