import Cart from "./cart"
import * as common from "./common"
declare var UIkit: any;

common.onGetAndDocumentLoaded("/webshop/product_data/" + window.productId, (value: any) => {
    common.addSidebarListeners();

    const {product, images, productData} = value;

    document.getElementById("name").innerText = product.name;

    const productPrice = product.price * product.smallest_multiple;
    const productUnit = product.smallest_multiple === 1 ? product.unit : `${product.smallest_multiple}${product.unit}`;
    document.getElementById("price").innerText = `${productPrice} kr/${productUnit}`;

    document.getElementById("smallest-multiple").setAttribute("step", product.smallest_multiple);

    document.getElementById("unit").innerText = product.unit;

    document.getElementById("description").innerHTML = product.description;

    const imagesDiv = document.getElementById("images");
    images.forEach((image: any) => {
        imagesDiv.innerHTML +=
            `<a class="product-image uk-inline" href='/static/product_images/${image.path}' data-caption="${image.caption}">
                 <img src='/static/product_images/${image.path}' alt="">
             </a>`;
    });

	const productAmount = <HTMLInputElement>document.querySelector(".product-amount");

	const id2item = new Map<number, any>();

	for (const cat of productData) {
		for (const item of cat.items) {
			id2item.set(item.id, item);
		}
	}

	function updateCartSum(cart: Cart) {
		if (cart.items.length > 0) {
			document.querySelector("#cart-sum").textContent = " (" + Cart.formatCurrency(cart.sum(id2item)) + ")";
		} else {
			document.querySelector("#cart-sum").textContent = "";
		}
	}

	function updateCountFromCart(cart: Cart) {
		productAmount.value = "" + cart.getItemCount(window.productId);
		updateCartSum(cart);
	}

	Cart.startLocalStorageSync(updateCountFromCart);
	updateCountFromCart(Cart.fromStorage());

	function setCartItem (updateField: boolean) {
		let newAmount = Cart.adjustItemCount(Number(productAmount.value), product);
		const cart = Cart.fromStorage();
		cart.setItem(window.productId, newAmount);
		cart.saveToStorage();
		if (updateField) productAmount.value = "" + newAmount;
		updateCartSum(cart);
	}
	productAmount.addEventListener("input", ev => setCartItem(false));
	productAmount.addEventListener("change", ev => setCartItem(true));

	document.querySelector(".number-add").addEventListener("click", ev => {
		productAmount.value = "" + (Number(productAmount.value) + product.smallest_multiple);
		setCartItem(true);
	});

	document.querySelector(".number-subtract").addEventListener("click", ev => {
		productAmount.value = "" + (Number(productAmount.value) - product.smallest_multiple);
		setCartItem(true);
	});
});
