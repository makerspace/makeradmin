import { render } from "preact";
import Cart from "./cart";
import * as common from "./common";
import { UNAUTHORIZED } from "./common";
import * as login from "./login";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import { LoadProductData, ProductData, Transaction } from "./payment_common";
import { Receipt } from "./receipt_common";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const HistoryPage = ({
    transactions,
    member,
    productData,
}: {
    transactions: Transaction[];
    member: member_t;
    productData: ProductData;
}) => {
    const cart = Cart.fromStorage();
    return (
        <>
            <Sidebar cart={{ cart, productData }} />
            <div id="content" className="purchase-history">
                <div className="content-centering">
                    <h2>Köphistorik</h2>
                    <h3>
                        #{member.member_number} {member.firstname}{" "}
                        {member.lastname}
                    </h3>
                    <div>
                        {transactions.map((transaction) => (
                            <Receipt
                                transaction={transaction}
                                detailed={false}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
};

common.documentLoaded().then(() => {
    const apiBasePath = window.apiBasePath;

    const transactions = common
        .ajax("GET", apiBasePath + "/webshop/member/current/transactions", null)
        .then((json) => json.data as Transaction[]);
    const member = LoadCurrentMemberInfo();
    const productData = LoadProductData();
    const root = document.querySelector("#root") as HTMLElement;

    Promise.all([transactions, member, productData])
        .then(([transactions, member, productData]) => {
            if (root != null) {
                root.innerHTML = "";
                render(
                    <HistoryPage
                        member={member}
                        transactions={transactions}
                        productData={productData}
                    />,
                    root,
                );
            }
        })
        .catch((json) => {
            // Probably Unauthorized, redirect to login page.
            if (json.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert(
                    "<h2>Misslyckades med att hämta köphistorik</h2>" +
                        common.get_error(json),
                );
            }
        });
});
