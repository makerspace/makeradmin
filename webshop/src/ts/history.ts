import * as common from "./common"
import Cart from "./cart"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
    const apiBasePath = window.apiBasePath;

    common.ajax("GET", apiBasePath + "/webshop/member/current/transactions", null)
    .then(json => {
        const rootElement = document.querySelector("#history-contents");
        rootElement.innerHTML = "";

        for (const transaction of json.data) {
            let cartItems = "";
            for (const item of transaction.content) {
                cartItems += `<div class="receipt-item">
                            <a class="product-title" href="/shop/product/${item.product.id}">${item.product.name}</a>
                            <span class="receipt-item-count">${item.count} ${item.product.unit}</span>
                            <span class="receipt-item-amount">${Cart.formatCurrency(Number(item.amount))}</span>
                        </div>`;
            }

            const elem = document.createElement("div");
            // transaction.status is one of {pending | completed | failed}
            elem.innerHTML = `<div class="history-item history-item-${transaction.status}">
                <h3><a href="/shop/receipt/${transaction.id}">${ new Date(transaction.created_at).toLocaleDateString("sv-SE") }</a></h3>
                <div class="receipt-items">
                    ${cartItems}
                </div>
                <div class="receipt-amount">
                    <span class="receipt-amount-value">${Cart.formatCurrency(Number(transaction.amount))}</span>
                </div>
            </div>`;
            rootElement.appendChild(elem.firstChild);
        }
    })
    .catch(json => {
        UIkit.modal.alert("<h2>Misslyckades med att hämta köphistorik</h2>" + common.get_error(json));
    });

    common.ajax("GET", apiBasePath + "/member/current", null)
    .then(json => {
        const member = json.data;
        document.querySelector("#member-header").textContent = `#${member.member_number} ${member.firstname} ${member.lastname}`;
    })
    .catch(json => {
        UIkit.modal.alert("<h2>Misslyckades med att hämta medlemsinformation</h2>" + common.get_error(json));
    });
});