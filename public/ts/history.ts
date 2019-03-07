import * as common from "./common"
import * as login from "./login"
import Cart from "./cart"
import {UNAUTHORIZED} from "./common";
declare var UIkit: any;

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;

    function format_receipt_status(transaction_status: string) {
        switch(transaction_status){
            case "pending": return "Ej bekräftad";
            case "completed": return "";
            case "failed": return "Misslyckad";
        };
        return "Okänd status";
    }

    const future1 = common.ajax("GET", apiBasePath + "/webshop/member/current/transactions", null);
    const future2 = common.ajax("GET", apiBasePath + "/member/current", null);

    const rootElement = <HTMLElement>document.querySelector("#history-contents");
    rootElement.innerHTML = "";

    Promise.all([future1, future2]).then(([transactionJson, memberJson]) => {

        for (const transaction of transactionJson.data) {
            let cartItems = "";
            for (const item of transaction.contents) {
                cartItems += `<div class="receipt-item">
                            <a class="product-title" href="/shop/product/${item.product.id}">${item.product.name}</a>
                            <span class="receipt-item-count">${item.count} ${item.product.unit}</span>
                            <span class="receipt-item-amount">${Cart.formatCurrency(Number(item.amount))}</span>
                        </div>`;
            }

            const elem = document.createElement("div");
            // transaction.status is one of {pending | completed | failed}
            elem.innerHTML = `<div class="history-item history-item-${transaction.status}">
                <a class="receipt-header" href="/shop/receipt/${transaction.id}">
                    <span>Kvitto ${transaction.id}</span>
                    <span class="receipt-date">${ new Date(transaction.created_at).toLocaleDateString("sv-SE") }</span>
                </a>
                <div class="receipt-items">
                    ${cartItems}
                </div>
                <div class="receipt-amount">
                    <span class="receipt-payment-status">${format_receipt_status(transaction.status)}</span>
                    <span class="receipt-amount-value">${Cart.formatCurrency(Number(transaction.amount))}</span>
                </div>
            </div>`;
            rootElement.appendChild(elem.firstChild);
        }

        const member = memberJson.data;
        document.querySelector("#member-header").textContent = `#${member.member_number} ${member.firstname} ${member.lastname}`;
    })
    .catch(json => {
        // Probably Unauthorized, redirect to login page.
        if (json.status === UNAUTHORIZED) {
            // Render login
            login.render_login(rootElement, null, null);
        } else {
            UIkit.modal.alert("<h2>Misslyckades med att hämta köphistorik</h2>" + common.get_error(json));
        }
    });
});