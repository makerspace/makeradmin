import Cart from "./cart"
import * as common from "./common"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
	const productID = Number(document.querySelector(".product-view").getAttribute("data-id"));

	const productAmount = <HTMLInputElement>document.querySelector(".product-amount");

	const data = JSON.parse(document.querySelector("#product-data").textContent);
	const id2item = new Map<number, any>();

	for (const cat of data) {
		for (const item of cat.items) {
			id2item.set(item.id, item);
		}
	}

	const item = id2item.get(productID);

	function updateCartSum(cart: Cart) {
		if (cart.items.length > 0) {
			document.querySelector("#cart-sum").textContent = " (" + Cart.formatCurrency(cart.sum(id2item)) + ")";
		} else {
			document.querySelector("#cart-sum").textContent = "";
		}
	}

	function updateCountFromCart(cart: Cart) {
		productAmount.value = "" + cart.getItemCount(productID);
		updateCartSum(cart);
	}

	Cart.startLocalStorageSync(updateCountFromCart);
	updateCountFromCart(Cart.fromStorage());

	function setCartItem (updateField: boolean) {
		let newAmount = Cart.adjustItemCount(Number(productAmount.value), item);
		const cart = Cart.fromStorage();
		cart.setItem(productID, newAmount);
		cart.saveToStorage();
		if (updateField) productAmount.value = "" + newAmount;
		updateCartSum(cart);
	}
	productAmount.addEventListener("input", ev => setCartItem(false));
	productAmount.addEventListener("change", ev => setCartItem(true));

	document.querySelector(".number-add").addEventListener("click", ev => {
		productAmount.value = "" + (Number(productAmount.value) + item.smallest_multiple);
		setCartItem(true);
	});

	document.querySelector(".number-subtract").addEventListener("click", ev => {
		productAmount.value = "" + (Number(productAmount.value) - item.smallest_multiple);
		setCartItem(true);
	});
});
