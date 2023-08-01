import * as common from "./common"
import * as login from "./login"
import Cart from "./cart"
import { UNAUTHORIZED } from "./common";
import { LoadProductData, Product, ProductData, Transaction, TransactionItem } from "./payment_common";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import { Sidebar } from "./sidebar";
import { render } from "preact";
declare var UIkit: any;

function format_receipt_status(transaction_status: string) {
    switch (transaction_status) {
        case "pending": return "Ej bekräftad";
        case "completed": return "";
        case "failed": return "Misslyckad";
    };
    return "Okänd status";
}

const ReceiptItem = ({ item }: { item: TransactionItem }) => {
    return <div className="receipt-item">
        <a className="product-title" href={`/shop/product/${item.product.id}`}>{item.product.name}</a>
        <span className="receipt-item-count">{item.count} {item.product.unit}</span>
        <span className="receipt-item-amount">{Cart.formatCurrency(Number(item.amount))}</span>
    </div>
}

const Receipt = ({ transaction }: { transaction: Transaction }) => {
    return <div className={`history-item history-item-${transaction.status}`}>
        <a className="receipt-header" href={`/shop/receipt/${transaction.id}`}>
            <span>Kvitto {transaction.id}</span>
            <span className="receipt-date">{new Date(transaction.created_at).toLocaleDateString("sv-SE")}</span>
        </a>
        <div className="receipt-items">
            {transaction.contents.map(item => <ReceiptItem item={item} />)}
        </div>
        <div className="receipt-amount">
            <span className="receipt-payment-status">{format_receipt_status(transaction.status)}</span>
            <span className="receipt-amount-value">{Cart.formatCurrency(Number(transaction.amount))}</span>
        </div>
    </div>
}

const HistoryPage = ({ transactions, member, productData }: { transactions: Transaction[], member: member_t, productData: ProductData }) => {
    const cart = Cart.fromStorage();
    return <>
        <Sidebar cart={{ cart, productData }} />
        <div id="content" className="purchase-history">
            <div className="content-centering">
                <h2>Köphistorik</h2>
                <h3>#{member.member_number} {member.firstname} {member.lastname}</h3>
                <div>
                    {transactions.map(transaction => <Receipt transaction={transaction} />)}
                </div>
            </div>
        </div>
    </>
}

common.documentLoaded().then(() => {
    const apiBasePath = window.apiBasePath;

    const transactions = common.ajax("GET", apiBasePath + "/webshop/member/current/transactions", null).then(json => json.data as Transaction[]);
    const member = LoadCurrentMemberInfo();
    const productData = LoadProductData();
    const root = document.querySelector("#root") as HTMLElement;

    Promise.all([transactions, member, productData]).then(([transactions, member, productData]) => {
        if (root != null) {
            root.innerHTML = "";
            render(
                <HistoryPage member={member} transactions={transactions} productData={productData} />,
                root
            );
        }
    })
        .catch(json => {
            // Probably Unauthorized, redirect to login page.
            if (json.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert("<h2>Misslyckades med att hämta köphistorik</h2>" + common.get_error(json));
            }
        });
});