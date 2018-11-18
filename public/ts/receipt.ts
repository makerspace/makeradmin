import * as common from "./common"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
    const content = document.getElementById("receipt-content");

    function pending() {
        content.innerHTML = `<h1>Din betalning har inte bekräftats ännu. Var god vänta.</h1>`;
        setTimeout(update, 3000);
    }

    function failed() {
        content.innerHTML = `<h1>Din betalning misslyckades</h1>`;
    }

    function completed(cart: any, transaction: any, member: any) {
        let cartHtml = cart.map((value: any) => {
            const [product, item] = value;

            return `
                <div class="receipt-item">
                    <a class="product-title" href="/shop/product/${product.id}">${product.name}</a>
                    <span class="receipt-item-count">${item.count} ${product.unit}</span>
                    <span class="receipt-item-amount">${item.amount} kr</span>
                </div>
            `;
        }).join("");

        // TODO Improved formatting.
        const createdAt = new Date(transaction.created_at).toLocaleString();

        content.innerHTML = `
            <h1>Tack för ditt köp!</h1>
            <div class="history-item history-item-${transaction.status}">
                <h3>${createdAt}<span class="receipt-id">Kvitto ${transaction.id}</span></h3>
                    <div class="receipt-items">
                        ${cartHtml}
                    </div>
                    <div class="receipt-amount">
                        <span>Summa</span>
                        <span class="receipt-amount-value">${transaction.amount} kr</span>
                    </div>
                    <div class="receipt-items">
                        <div class="receipt-item">
                            <span class="product-title">Medlem</span>
                            <span class="receipt-item-amount" style="min-width: 200px;">${member.firstname} ${member.lastname} #${member.member_number}</span>
                        </div>
                    </div>
                </div>
                <div class="receipt-message">
                    <p>Ett kvitto har också skickats via email.</p>
                    <p>Stockholm Makerspace - Drottning Kristinas väg 53, 114 28 Stockholm</p>
                </div>
        `;
    }

    function update() {
        content.innerHTML = '';
        common
            .ajax("GET", window.apiBasePath + "/webshop/receipt/" + window.transactionId, {})
            .then(json => {
                const {cart, transaction, member} = json.data;
                if (transaction.status === "failed") {
                    failed();
                }
                else if (transaction.status === "completed") {
                    completed(cart, transaction, member);
                }
                else {
                    pending();
                }
            })
            .catch(json => {
                pending();
            });
    }

    update();
});
