import Cart from "./cart"
import * as common from "./common"
import {UNAUTHORIZED} from "./common";
import {renderSidebarCategories} from "./category"
import {initializeStripe, pay} from "./payment_common"
declare var UIkit: any;

common.onGetAndDocumentLoaded("/webshop/product_data", (productData: any) => {
	common.addSidebarListeners();

	renderSidebarCategories(productData);

	const id2item = new Map<number, any>();

	for (const category of productData) {
		for (const item of category.items) {
			id2item.set(item.id, item);
		}
	}

	function setCartItem(productID: number, count: number) {
		let cart = Cart.fromStorage();
		cart.setItem(productID, count);
		cart.saveToStorage();
		common.updateCartSum(cart, id2item);
	}

	function createElements(cart: Cart) {
		common.updateCartSum(cart, id2item);
		document.querySelector("#cart").innerHTML = "";

		if (cart.items.length == 0) {
			document.querySelector("#cart").innerHTML = "<p class='empty-cart-text'>Du har inga produkter i varukorgen.</p>";
			(<HTMLButtonElement>document.querySelector("#pay-button")).disabled = true;
			return;
		}

		(<HTMLButtonElement>document.querySelector("#pay-button")).disabled = false;

		for (const cartItem of cart.items) {
			const item = id2item.get(cartItem.id);
			let price = item.price;
			price *= item.smallest_multiple;

			let baseStr = item.smallest_multiple > 1 ? item.smallest_multiple + item.unit : item.unit;

			const li = document.createElement("li");
			li.innerHTML = `
				<div class="product">
					<div class="product-line">
						<a class="product-title" href="product/${item.id}">${item.name}</a>
						<span class="product-price">${price} ${Cart.currency}/${baseStr}</span>
					</div>
					<div class="product-input product-line">
						<input type="number" min=0 max=9999 step=${item.smallest_multiple} placeholder="0" class="product-amount"></input>
						<span class="product-unit">${item.unit}</span>
						<button type="button" class="product-delete uk-button uk-button-small uk-button-danger" uk-icon="trash" ></button>
					</div>
				</div>`;
			id2item.set(item.id, item);

			// Handle deleting products
			li.querySelector(".product-delete").addEventListener("click", ev => {
				ev.preventDefault();
				setCartItem(item.id, 0);
				li.remove();
			});

			const productAmount = <HTMLInputElement>li.querySelector(".product-amount");
			// Select everything in the textfield when clicking on it
			productAmount.onclick = () => {
				productAmount.select();
			};

			productAmount.oninput = ev => {
				let newAmount = Cart.adjustItemCount(Number(productAmount.value), item);
				setCartItem(item.id, newAmount);
			};

			productAmount.onchange = ev => {
				let newAmount = Cart.adjustItemCount(Number(productAmount.value), item);
				setCartItem(item.id, newAmount);
				productAmount.value = "" + newAmount;
			};

			productAmount.value = "" + cartItem.count;
			document.querySelector("#cart").appendChild(li);
		}
	}

	initializeStripe();

	function pay_config() {
		function initiate_payment(result: any){
			let cart = Cart.fromStorage();
			return common.ajax("POST", window.apiBasePath + "/webshop/pay", {
				cart: cart.items,
				expected_sum: cart.sum(id2item),
				stripe_payment_method_id: result.paymentMethod.id,
			})
		}
		function on_payment_success(json: any){
			new Cart([]).saveToStorage();
		}
		function on_failure(json: any){
			if (json.status === UNAUTHORIZED) {
				UIkit.modal.alert("<h2>Betalningen misslyckades</h2>Du är inte inloggad");
			} else {
				UIkit.modal.alert("<h2>Betalningen misslyckades</h2>" + common.get_error(json));
			}
		}
		return {
			initiate_payment: initiate_payment,
			on_payment_success: on_payment_success,
			on_failure: on_failure,
		};
	}
	const payment_config = pay_config();

	function login() {
		common.ajax("POST", window.apiBasePath + "/member/send_access_token", {
			user_tag: (<HTMLInputElement>document.querySelector("#email")).value,
			redirect: "/shop/cart"
		}).then(json => {
			UIkit.modal.alert("En inloggningslänk har skickats via email");
		}).catch(json => {
			if (json.status == "not found") {
				UIkit.modal.alert("Ingen medlem med denna email hittades");
			} else {
				UIkit.modal.alert("<h2>Error</h2>" + common.get_error(json));
			}
		});
	}

	function setLoggedIn(loggedIn: boolean) {
		document.querySelector("#pay-login").classList.toggle("active", !loggedIn);
		document.querySelector("#pay").classList.toggle("active", loggedIn);
	}

	common.refreshLoggedIn((loggedIn, permissions) => {
		setLoggedIn(loggedIn);
	});

	Cart.startLocalStorageSync(createElements);
	createElements(Cart.fromStorage());

	document.querySelector("#pay-button").addEventListener("click", ev => {
		ev.preventDefault();
		pay(payment_config);
	});

	document.querySelector("#pay-login form").addEventListener("submit", ev => {
		ev.preventDefault();
		login();
	});
});
