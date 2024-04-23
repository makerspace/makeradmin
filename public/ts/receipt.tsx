import { render } from "preact";
import { useEffect, useState } from "preact/hooks";
import Cart from "./cart";
import {
    UNAUTHORIZED,
    ajax,
    documentLoaded,
    get_error,
    show_error,
} from "./common";
import * as login from "./login";
import { LoadCurrentMemberInfo, member_t } from "./member_common";
import {
    LoadProductData,
    Product,
    ProductData,
    Transaction,
} from "./payment_common";
import { Receipt } from "./receipt_common";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

type ReceiptResponse = {
    member: member_t;
    transaction: Transaction;
    cart: Product[];
};

const ReceiptWithInfo = ({ transactionId }: { transactionId: number }) => {
    const [receiptData, setReceiptData] = useState<ReceiptResponse | null>(
        null,
    );

    useEffect(() => {
        let id: NodeJS.Timeout;
        const refresh = async () => {
            try {
                const data = (
                    await ajax(
                        "GET",
                        window.apiBasePath +
                            "/webshop/member/current/receipt/" +
                            transactionId,
                        {},
                    )
                ).data as ReceiptResponse;
                setReceiptData(data);
            } catch (e) {
                console.error(e);
                show_error("Kunde inte hitta kvittot", e);
                clearInterval(id);
            }
        };
        id = setInterval(refresh, 1000);
        refresh();
        return () => clearInterval(id);
    }, []);

    if (receiptData === null) return null;

    const { transaction, member } = receiptData;

    return (
        <>
            {transaction.status === "completed" && <h1>Tack för ditt köp!</h1>}
            <Receipt
                transaction={transaction}
                member={member}
                detailed={true}
            />
            {transaction.status === "completed" && (
                <div class="receipt-message">
                    <p>Ett kvitto har också skickats via email.</p>
                    <p>
                        Stockholm Makerspace - Drottning Kristinas väg 53, 114
                        28 Stockholm
                    </p>
                </div>
            )}
        </>
    );
};

const ReceiptPage = ({
    transactionId,
    productData,
}: {
    transactionId: number;
    productData: ProductData;
}) => {
    const cart = Cart.fromStorage();

    return (
        <>
            <Sidebar cart={{ cart, productData }} />
            <div id="content" className="receipt">
                <div className="content-centering">
                    <div id="receipt-content">
                        <ReceiptWithInfo transactionId={transactionId} />
                    </div>
                </div>
            </div>
        </>
    );
};

documentLoaded().then(() => {
    const apiBasePath = window.apiBasePath;

    const member = LoadCurrentMemberInfo();
    const productData = LoadProductData();
    const root = document.querySelector("#root") as HTMLElement;

    Promise.all([member, productData])
        .then(([member, productData]) => {
            if (root != null) {
                root.innerHTML = "";
                render(
                    <ReceiptPage
                        transactionId={window.transactionId}
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
                    "<h2>Misslyckades med att hämta kvittot</h2>" +
                        get_error(json),
                );
            }
        });
});
