/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import Cart from "./cart"
import * as common from "./common"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
	const apiBasePath = window.apiBasePath;
	const data = JSON.parse(document.querySelector("#product-data").textContent);
	const id2item = new Map<number, any>();

	// Used to prevent clicking the 'Pay' button twice
	const duplicatePurchaseRand = (100000000 * Math.random()) | 0;

	for (const cat of data) {
		for (const item of cat.items) {
			id2item.set(item.id, item);
		}
	}

	function setCartItem(productID: number, count: number) {
		let cart = Cart.fromStorage();
		cart.setItem(productID, count);
		cart.saveToStorage();
		updateCartSum(cart);
	}

	function createElements(cart: Cart) {
		updateCartSum(cart);
		document.querySelector("#cart").innerHTML = "";

		if (cart.items.length == 0) {
			document.querySelector("#cart").innerHTML = "<p class='empty-cart'>Du har inga produkter i varukorgen.</p>";
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
			li.innerHTML =
				`<div class="product">
					<a class="product-title" href="product/${item.id}">${item.name}</a>
					<span class="product-price">${price} ${Cart.currency}/${baseStr}</span>
					<input type="number" min=0 max=9999 step=${item.smallest_multiple} placeholder="0" class="product-amount"></input>
					<span class="product-unit">${item.unit}</span>
					<button type="button" class="product-delete uk-button uk-button-small uk-button-danger" uk-icon="trash" ></button>
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

	function initializeStripe() {
		// Create a Stripe client.
		const stripe = Stripe(window.stripeKey);
		// Create an instance of Elements.
		const elements = stripe.elements({ locale: "sv" });
		// Custom styling can be passed to options when creating an Element.
		const stripeStyle = {
			base: {
				color: '#32325d',
				lineHeight: '18px',
				fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
				fontSmoothing: 'antialiased',
				fontSize: '16px',
				'::placeholder': {
					color: '#aab7c4'
				}
			},
			invalid: {
				color: '#fa755a',
				iconColor: '#fa755a'
			}
		};

		// Create an instance of the card Element.
		const card = elements.create('card', { style: stripeStyle });

		// Add an instance of the card Element into the `card-element` <div>.
		card.mount('#card-element');
		return { stripe, card };
	}

	const { stripe, card } = initializeStripe();

	function updateCartSum(cart: Cart) {
		document.querySelector("#cart-sum").textContent = " " + Cart.formatCurrency(cart.sum(id2item));
	}

	let waitingForPaymentResponse = false;

	function pay() {
		// Don't allow any clicks while waiting for a response from the server
		if (waitingForPaymentResponse) {
			return;
		}

		waitingForPaymentResponse = true;

		const spinner = document.querySelector(".progress-spinner");
		spinner.classList.add("progress-spinner-visible");
		let errorElement = document.getElementById('card-errors');
		errorElement.textContent = "";

		stripe.createSource(card).then(function(result) {
			if (result.error) {
				spinner.classList.remove("progress-spinner-visible");
				// Inform the user if there was an error.
				errorElement.textContent = result.error.message;
				waitingForPaymentResponse = false;
			} else {
				let cart = Cart.fromStorage();
				common.ajax("POST", apiBasePath + "/webshop/pay", {
					cart: cart.items,
					expectedSum: cart.sum(id2item),
					stripeSource: result.source.id,
					stripeThreeDSecure: result.source.card.three_d_secure,
					duplicatePurchaseRand: duplicatePurchaseRand,
				}).then(json => {
					spinner.classList.remove("progress-spinner-visible");
					waitingForPaymentResponse = false;
					new Cart([]).saveToStorage();
					if (json.data.redirect !== undefined) {
						window.location.href = json.data.redirect;
					} else {
						window.location.href = "receipt/" + json.data.transaction_id;
					}
					// UIkit.modal.alert("Betalningen har genomförts");
				}).catch(json => {
					spinner.classList.remove("progress-spinner-visible");
					waitingForPaymentResponse = false;
					if (json.message == "Unauthorized") {
						UIkit.modal.alert("<h2>Betalningen misslyckades</h2>Du är inte inloggad");
					} else {
						UIkit.modal.alert("<h2>Betalningen misslyckades</h2>" + common.get_error(json));
					}
				});
			}
		});
	}

	function login() {
		common.ajax("POST", apiBasePath + "/member/send_access_token", {
			user_tag: (<HTMLInputElement>document.querySelector("#email")).value,
			redirect: "shop/cart"
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

	document.querySelector("#pay").addEventListener("submit", ev => {
		ev.preventDefault();
		pay();
	});

	document.querySelector("#pay-login form").addEventListener("submit", ev => {
		ev.preventDefault();
		login();
	});
});
